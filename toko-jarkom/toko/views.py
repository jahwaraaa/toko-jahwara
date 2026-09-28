from bson import ObjectId
from bson.errors import InvalidId
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.admin.views.decorators import staff_member_required
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .db import db
from .forms import PAYMENT_STATUS_CHOICES, ProductForm, PurchaseFilterForm, PurchaseForm


PAYMENT_STATUS_LABELS = dict(PAYMENT_STATUS_CHOICES)


def health_check(request):
	return HttpResponse('ok')


def index(request):
	products = list(db.supply.find().sort('nama', 1))
	for product in products:
		product['product_id'] = str(product.pop('_id'))
	total_stock = sum(product.get('stok', 0) for product in products)
	low_stock_count = sum(product.get('stok', 0) < 10 for product in products)
	return render(request, 'index.html', {
		'products': products,
		'product_count': len(products),
		'total_stock': total_stock,
		'low_stock_count': low_stock_count,
	})


@staff_member_required
def admin_dashboard(request):
	products = list(db.supply.find().sort('nama', 1))
	recent_purchases = list(
		db.purchases.find().sort([('tanggal', -1), ('dibuat_pada', -1)]).limit(8)
	)
	for purchase in recent_purchases:
		purchase['purchase_id'] = str(purchase.pop('_id'))
		purchase['status_label'] = PAYMENT_STATUS_LABELS.get(
			purchase.get('status_pembayaran'), 'Tidak diketahui',
		)
	return render(request, 'admin_dashboard.html', {
		'product_count': len(products),
		'low_stock_count': sum(product.get('stok', 0) < 10 for product in products),
		'total_stock': sum(product.get('stok', 0) for product in products),
		'purchase_count': db.purchases.count_documents({}),
		'recent_purchases': recent_purchases,
	})


def login_view(request):
	if request.user.is_authenticated:
		return redirect('index')
	form = AuthenticationForm(request, data=request.POST or None)
	if request.method == 'POST' and form.is_valid():
		login(request, form.get_user())
		next_url = request.POST.get('next') or request.GET.get('next')
		if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
			return redirect(next_url)
		return redirect('index')
	return render(request, 'auth.html', {
		'form': form,
		'page_title': 'Selamat datang kembali',
		'page_intro': 'Masuk untuk mengelola katalog dan stok toko.',
		'submit_label': 'Masuk ke akun',
		'switch_prompt': 'Belum punya akun?',
		'switch_label': 'Daftar di sini',
		'switch_url': 'register',
		'next': request.GET.get('next', ''),
	})


def register_view(request):
	if request.user.is_authenticated:
		return redirect('index')
	form = UserCreationForm(request.POST or None)
	if request.method == 'POST' and form.is_valid():
		user = form.save()
		login(request, user)
		messages.success(request, 'Akun berhasil dibuat. Selamat datang!')
		return redirect('index')
	return render(request, 'auth.html', {
		'form': form,
		'page_title': 'Buat akun pengelola',
		'page_intro': 'Satu akun untuk mulai mengatur inventaris toko.',
		'submit_label': 'Buat akun',
		'switch_prompt': 'Sudah punya akun?',
		'switch_label': 'Masuk di sini',
		'switch_url': 'login',
	})


@require_POST
def logout_view(request):
	logout(request)
	return redirect('index')


@login_required
def product_create(request):
	form = ProductForm(request.POST or None)
	if request.method == 'POST' and form.is_valid():
		db.supply.insert_one(form.cleaned_data)
		messages.success(request, 'Produk berhasil ditambahkan.')
		return redirect('index')
	return render(request, 'product_form.html', {
		'form': form,
		'page_title': 'Tambah produk',
		'submit_label': 'Simpan produk',
	})


def _get_product(product_id):
	try:
		product = db.supply.find_one({'_id': ObjectId(product_id)})
	except (InvalidId, TypeError):
		raise Http404('Produk tidak ditemukan.')
	if product is None:
		raise Http404('Produk tidak ditemukan.')
	return product


@login_required
def product_edit(request, product_id):
	product = _get_product(product_id)
	form = ProductForm(request.POST or None, initial={
		'nama': product.get('nama', ''),
		'harga': product.get('harga', 0),
		'stok': product.get('stok', 0),
	})
	if request.method == 'POST' and form.is_valid():
		db.supply.update_one(
			{'_id': product['_id']},
			{'$set': form.cleaned_data},
		)
		messages.success(request, 'Produk berhasil diperbarui.')
		return redirect('index')
	return render(request, 'product_form.html', {
		'form': form,
		'page_title': 'Edit produk',
		'submit_label': 'Simpan perubahan',
	})


@login_required
@require_POST
def product_delete(request, product_id):
	product = _get_product(product_id)
	db.supply.delete_one({'_id': product['_id']})
	messages.success(request, 'Produk berhasil dihapus.')
	return redirect('index')


@login_required
def purchase_create(request):
	products = list(db.supply.find().sort('nama', 1))
	if not products:
		messages.error(request, 'Tambahkan produk ke katalog sebelum mencatat pembelian.')
		return redirect('index')
	form = PurchaseForm(request.POST or None, products=products)
	if request.method == 'POST' and form.is_valid():
		purchase = {
			'supplier': form.cleaned_data['supplier'].strip(),
			'tanggal': form.cleaned_data['tanggal'].isoformat(),
			'status_pembayaran': form.cleaned_data['status_pembayaran'],
			'items': form.cleaned_data['items'],
			'total': form.cleaned_data['total'],
			'dibuat_oleh': request.user.username,
			'dibuat_pada': timezone.now().isoformat(),
		}
		for item in purchase['items']:
			db.supply.update_one(
				{'_id': ObjectId(item['product_id'])},
				{'$inc': {'stok': item['jumlah']}},
			)
		result = db.purchases.insert_one(purchase)
		messages.success(request, 'Pembelian berhasil dicatat dan stok produk diperbarui.')
		return redirect('purchase_detail', purchase_id=str(result.inserted_id))
	return render(request, 'purchase_form.html', {
		'form': form,
		'page_title': 'Buat pembelian',
		'submit_label': 'Simpan pembelian',
		'products_json': [
			{'id': str(product['_id']), 'harga': product.get('harga', 0)}
			for product in products
		],
	})


@login_required
def purchase_history(request):
	suppliers = db.purchases.distinct('supplier')
	form = PurchaseFilterForm(request.GET or None, suppliers=suppliers)
	query = {}
	if form.is_valid():
		if form.cleaned_data['supplier']:
			query['supplier'] = form.cleaned_data['supplier']
		if form.cleaned_data['status_pembayaran']:
			query['status_pembayaran'] = form.cleaned_data['status_pembayaran']
		date_range = {}
		if form.cleaned_data['tanggal_dari']:
			date_range['$gte'] = form.cleaned_data['tanggal_dari'].isoformat()
		if form.cleaned_data['tanggal_sampai']:
			date_range['$lte'] = form.cleaned_data['tanggal_sampai'].isoformat()
		if date_range:
			query['tanggal'] = date_range
	purchases = list(db.purchases.find(query).sort([('tanggal', -1), ('dibuat_pada', -1)]))
	for purchase in purchases:
		purchase['purchase_id'] = str(purchase.pop('_id'))
		purchase['status_label'] = PAYMENT_STATUS_LABELS.get(
			purchase.get('status_pembayaran'), 'Tidak diketahui',
		)
	return render(request, 'purchase_history.html', {
		'form': form,
		'purchases': purchases,
		'purchase_count': len(purchases),
	})


@login_required
def purchase_detail(request, purchase_id):
	try:
		purchase = db.purchases.find_one({'_id': ObjectId(purchase_id)})
	except (InvalidId, TypeError):
		raise Http404('Pembelian tidak ditemukan.')
	if purchase is None:
		raise Http404('Pembelian tidak ditemukan.')
	purchase['status_label'] = PAYMENT_STATUS_LABELS.get(
		purchase.get('status_pembayaran'), 'Tidak diketahui',
	)
	return render(request, 'purchase_detail.html', {'purchase': purchase})

from django import forms
from django.utils import timezone


class ProductForm(forms.Form):
	nama = forms.CharField(
		label='Nama produk',
		max_length=100,
		widget=forms.TextInput(attrs={'placeholder': 'Contoh: Kabel LAN Cat6'}),
	)
	harga = forms.IntegerField(
		label='Harga (Rp)',
		min_value=0,
		widget=forms.NumberInput(attrs={'min': 0, 'placeholder': '25000'}),
	)
	stok = forms.IntegerField(
		label='Jumlah stok',
		min_value=0,
		widget=forms.NumberInput(attrs={'min': 0, 'placeholder': '40'}),
	)

	def clean_nama(self):
		return self.cleaned_data['nama'].strip()


PAYMENT_STATUS_CHOICES = [
	('belum_dibayar', 'Belum dibayar'),
	('dibayar_sebagian', 'Dibayar sebagian'),
	('lunas', 'Lunas'),
]


class PurchaseForm(forms.Form):
	supplier = forms.CharField(label='Nama supplier', max_length=120)
	tanggal = forms.DateField(
		label='Tanggal pembelian',
		initial=timezone.localdate,
		widget=forms.DateInput(attrs={'type': 'date'}),
	)
	status_pembayaran = forms.ChoiceField(
		label='Status pembayaran',
		choices=PAYMENT_STATUS_CHOICES,
	)
	jumlah_item = forms.IntegerField(
		min_value=1,
		max_value=12,
		initial=1,
		widget=forms.HiddenInput,
	)

	def __init__(self, *args, products, **kwargs):
		self.products_by_id = {str(product['_id']): product for product in products}
		super().__init__(*args, **kwargs)
		try:
			self.item_count = int(self.data.get('jumlah_item', 1)) if self.is_bound else 1
		except (TypeError, ValueError):
			self.item_count = 1
		self.item_count = max(1, min(self.item_count, 12))
		choices = [
			(product_id, product.get('nama', 'Produk'))
			for product_id, product in self.products_by_id.items()
		]
		for index in range(self.item_count):
			self.fields[f'produk_{index}'] = forms.ChoiceField(
				label='Produk',
				choices=choices,
			)
			self.fields[f'jumlah_{index}'] = forms.IntegerField(
				label='Jumlah',
				min_value=1,
				initial=1,
			)
			self.fields[f'harga_{index}'] = forms.IntegerField(
				label='Harga beli per unit (Rp)',
				min_value=0,
				initial=0,
			)

	@property
	def item_rows(self):
		return [
			(self[f'produk_{index}'], self[f'jumlah_{index}'], self[f'harga_{index}'])
			for index in range(self.item_count)
		]

	def clean(self):
		cleaned_data = super().clean()
		items = []
		for index in range(self.item_count):
			product_id = cleaned_data.get(f'produk_{index}')
			quantity = cleaned_data.get(f'jumlah_{index}')
			unit_price = cleaned_data.get(f'harga_{index}')
			product = self.products_by_id.get(product_id)
			if product and quantity is not None and unit_price is not None:
				items.append({
					'product_id': product_id,
					'nama': product.get('nama', ''),
					'jumlah': quantity,
					'harga': unit_price,
					'subtotal': quantity * unit_price,
				})
		cleaned_data['items'] = items
		cleaned_data['total'] = sum(item['subtotal'] for item in items)
		return cleaned_data


class PurchaseFilterForm(forms.Form):
	supplier = forms.ChoiceField(label='Supplier', required=False)
	tanggal_dari = forms.DateField(
		label='Dari tanggal',
		required=False,
		widget=forms.DateInput(attrs={'type': 'date'}),
	)
	tanggal_sampai = forms.DateField(
		label='Sampai tanggal',
		required=False,
		widget=forms.DateInput(attrs={'type': 'date'}),
	)
	status_pembayaran = forms.ChoiceField(
		label='Status pembayaran',
		required=False,
		choices=[('', 'Semua status'), *PAYMENT_STATUS_CHOICES],
	)

	def __init__(self, *args, suppliers=(), **kwargs):
		super().__init__(*args, **kwargs)
		self.fields['supplier'].choices = [('', 'Semua supplier')] + [
			(supplier, supplier) for supplier in suppliers
		]

	def clean(self):
		cleaned_data = super().clean()
		start = cleaned_data.get('tanggal_dari')
		end = cleaned_data.get('tanggal_sampai')
		if start and end and start > end:
			self.add_error('tanggal_sampai', 'Tanggal akhir harus sama atau setelah tanggal awal.')
		return cleaned_data
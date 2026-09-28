from unittest.mock import patch

from bson import ObjectId
from django.contrib.auth.models import User
from django.test import TestCase


class InventoryViewTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(username='store-manager', password='StrongPass-9284!')
		self.product_id = ObjectId()
		self.product = {
			'_id': self.product_id,
			'nama': 'Kabel LAN 5m',
			'harga': 25000,
			'stok': 40,
		}

	@patch('toko.views.db')
	def test_dashboard_lists_mongodb_products(self, mocked_db):
		mocked_db.supply.find.return_value.sort.return_value = [self.product.copy()]

		response = self.client.get('/')

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Kabel LAN 5m')
		self.assertContains(response, '1 item')

	def test_product_creation_requires_login(self):
		response = self.client.get('/products/new/')

		self.assertRedirects(response, '/login/?next=/products/new/')

	@patch('toko.views.db')
	def test_logged_in_user_can_create_product(self, mocked_db):
		self.client.force_login(self.user)

		response = self.client.post('/products/new/', {
			'nama': 'Router Baru',
			'harga': '150000',
			'stok': '12',
		})

		self.assertRedirects(response, '/')
		mocked_db.supply.insert_one.assert_called_once_with({
			'nama': 'Router Baru',
			'harga': 150000,
			'stok': 12,
		})

	@patch('toko.views.db')
	def test_logged_in_user_can_edit_product(self, mocked_db):
		self.client.force_login(self.user)
		mocked_db.supply.find_one.return_value = self.product

		response = self.client.post(f'/products/{self.product_id}/edit/', {
			'nama': 'Kabel LAN 10m',
			'harga': '35000',
			'stok': '8',
		})

		self.assertRedirects(response, '/')
		mocked_db.supply.update_one.assert_called_once_with(
			{'_id': self.product_id},
			{'$set': {'nama': 'Kabel LAN 10m', 'harga': 35000, 'stok': 8}},
		)

	@patch('toko.views.db')
	def test_logged_in_user_can_delete_product(self, mocked_db):
		self.client.force_login(self.user)
		mocked_db.supply.find_one.return_value = self.product

		response = self.client.post(f'/products/{self.product_id}/delete/')

		self.assertRedirects(response, '/')
		mocked_db.supply.delete_one.assert_called_once_with({'_id': self.product_id})

	def test_registration_creates_and_signs_in_user(self):
		response = self.client.post('/register/', {
			'username': 'new-manager',
			'password1': 'StrongPass-9284!',
			'password2': 'StrongPass-9284!',
		})

		self.assertEqual(response.status_code, 302)
		self.assertEqual(response.url, '/')
		self.assertTrue(User.objects.filter(username='new-manager').exists())
		self.assertIn('_auth_user_id', self.client.session)

	@patch('toko.views.db')
	def test_admin_dashboard_requires_staff_and_shows_purchase_summary(self, mocked_db):
		response = self.client.get('/admin-panel/')
		self.assertEqual(response.status_code, 302)

		staff_user = User.objects.create_user(
			username='store-admin',
			password='StrongPass-9284!',
			is_staff=True,
		)
		self.client.force_login(staff_user)
		mocked_db.supply.find.return_value.sort.return_value = [self.product.copy()]
		mocked_db.purchases.find.return_value.sort.return_value.limit.return_value = []
		mocked_db.purchases.count_documents.return_value = 0

		response = self.client.get('/admin-panel/')

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Administrasi Toko Jahwara')
		self.assertContains(response, 'Produk terdaftar')

	def test_purchase_creation_requires_login(self):
		response = self.client.get('/purchases/new/')

		self.assertRedirects(response, '/login/?next=/purchases/new/')

	@patch('toko.views.db')
	def test_purchase_form_renders_for_logged_in_user(self, mocked_db):
		self.client.force_login(self.user)
		mocked_db.supply.find.return_value.sort.return_value = [self.product.copy()]

		response = self.client.get('/purchases/new/')

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Nama supplier')
		self.assertContains(response, 'Kabel LAN 5m')
		self.assertContains(response, 'Tambah baris')

	@patch('toko.views.db')
	def test_purchase_creation_increases_stock_and_saves_total(self, mocked_db):
		self.client.force_login(self.user)
		mocked_db.supply.find.return_value.sort.return_value = [self.product.copy()]
		mocked_db.purchases.insert_one.return_value.inserted_id = ObjectId()

		response = self.client.post('/purchases/new/', {
			'supplier': 'Supplier Prima',
			'tanggal': '2026-09-28',
			'status_pembayaran': 'belum_dibayar',
			'jumlah_item': '1',
			f'produk_0': str(self.product_id),
			'jumlah_0': '5',
			'harga_0': '18000',
		})

		self.assertEqual(response.status_code, 302)
		mocked_db.supply.update_one.assert_called_once_with(
			{'_id': self.product_id}, {'$inc': {'stok': 5}},
		)
		purchase = mocked_db.purchases.insert_one.call_args.args[0]
		self.assertEqual(purchase['total'], 90000)
		self.assertEqual(purchase['items'][0]['subtotal'], 90000)
		self.assertEqual(purchase['supplier'], 'Supplier Prima')

	@patch('toko.views.db')
	def test_purchase_history_filters_by_supplier_and_date(self, mocked_db):
		self.client.force_login(self.user)
		mocked_db.purchases.distinct.return_value = ['Supplier Prima']
		mocked_db.purchases.find.return_value.sort.return_value = []

		response = self.client.get('/purchases/', {
			'supplier': 'Supplier Prima',
			'tanggal_dari': '2026-09-01',
			'tanggal_sampai': '2026-09-30',
		})

		self.assertEqual(response.status_code, 200)
		mocked_db.purchases.find.assert_called_once_with({
			'supplier': 'Supplier Prima',
			'tanggal': {'$gte': '2026-09-01', '$lte': '2026-09-30'},
		})

	@patch('toko.views.db')
	def test_purchase_detail_shows_saved_items(self, mocked_db):
		self.client.force_login(self.user)
		purchase_id = ObjectId()
		mocked_db.purchases.find_one.return_value = {
			'_id': purchase_id,
			'supplier': 'Supplier Prima',
			'tanggal': '2026-09-28',
			'status_pembayaran': 'lunas',
			'dibuat_oleh': self.user.username,
			'items': [{'nama': 'Kabel LAN 5m', 'jumlah': 5, 'harga': 18000, 'subtotal': 90000}],
			'total': 90000,
		}

		response = self.client.get(f'/purchases/{purchase_id}/')

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Supplier Prima')
		self.assertContains(response, 'Kabel LAN 5m')
		self.assertContains(response, 'Rp 90000')

"""A small starting test suite for the order desk."""

from pathlib import Path
import tempfile
import unittest

from supplydesk.service import OrderService


class OrderSmokeTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "state.json"
        self.service = OrderService(self.path)

    def test_regular_pickup_quote(self):
        quote = self.service.quote("regular", [{"product_id": "notebook", "quantity": 2}])
        self.assertEqual(quote["subtotal_cents"], 1000)
        self.assertEqual(quote["discount_cents"], 0)
        self.assertEqual(quote["delivery_cents"], 0)
        self.assertEqual(quote["total_cents"], 1000)

    def test_student_delivery_quote(self):
        quote = self.service.quote("student", [{"product_id": "hoodie", "quantity": 2}], "delivery")
        self.assertEqual(quote["discount_cents"], 800)
        self.assertEqual(quote["delivery_cents"], 600)
        self.assertEqual(quote["total_cents"], 7800)

    def test_order_can_be_reopened(self):
        order = self.service.place_order("regular", [{"product_id": "mug", "quantity": 1}])
        self.assertEqual(order["order_id"], "ORD-0001")
        self.assertEqual(order["status"], "placed")
        self.assertEqual(OrderService(self.path).get_order(order["order_id"]), order)

    def test_cancel_order_restores_stock(self):
        before = self.service.catalog()
        order = self.service.place_order("regular", [{"product_id": "pen-pack", "quantity": 2}])
        cancelled = self.service.cancel_order(order["order_id"])
        self.assertEqual(cancelled["status"], "cancelled")
        self.assertEqual(self.service.catalog(), before)

# Normal behaviour
    def test_placed_order(self):
        order = self.service.place_order("regular", [{"product_id": "mug", "quantity": 1}])
        placed = self.service.get_order(order["order_id"])
        self.assertEqual(placed["status"], "placed")
        self.assertEqual(OrderService(self.path).get_order(order["order_id"]), placed)

    def test_cancel_order(self):
        order = self.service.place_order("regular", [{"product_id": "pen-pack", "quantity": 2}])
        cancelled = self.service.cancel_order(order["order_id"])
        self.assertEqual(cancelled["status"], "cancelled")
        self.assertEqual(OrderService(self.path).get_order(order["order_id"]), cancelled)

    def test_get_order(self):
        order = self.service.place_order("regular", [{"product_id": "mug", "quantity": 1}])
        retrieved = self.service.get_order(order["order_id"])
        self.assertEqual(retrieved, order)

    def test_catalog(self):
        catalog = self.service.catalog()
        self.assertEqual(len(catalog), 5)
        self.assertEqual(catalog[0]["product_id"], "notebook")
        self.assertEqual(catalog[0]["stock"], 20)

# Boundary behaviour
    def test_cannot_place_order_with_zero_quantity(self):
        with self.assertRaises(ValueError):
            self.service.place_order("regular", [{"product_id": "mug", "quantity": 0}])

    def test_cannot_place_order_with_negative_quantity(self):
        with self.assertRaises(ValueError):
            self.service.place_order("regular", [{"product_id": "mug", "quantity": -1}])

    def test_cannot_place_order_with_insufficient_stock(self):
        with self.assertRaises(ValueError):
            self.service.place_order("regular", [{"product_id": "notebook", "quantity": 200}])

    def test_cannot_place_empty_order(self):
        with self.assertRaises(ValueError):
            self.service.place_order("regular", [])
    
# Invalid/exceptional behaviour
    def test_cannot_cancel_already_cancelled_order(self):
        order = self.service.place_order("regular", [{"product_id": "pen-pack", "quantity": 2}])
        self.service.cancel_order(order["order_id"])
        with self.assertRaises(ValueError):
            self.service.cancel_order(order["order_id"])

    def test_cannot_place_cancelled_order(self):
        order = self.service.place_order("regular", [{"product_id": "pen-pack", "quantity": 2}])
        self.service.cancel_order(order["order_id"])
        with self.assertRaises(ValueError):
            self.service.get_order(order["order_id"])

    def test_cannot_order_unknown_product(self):
        with self.assertRaises(ValueError):
            self.service.place_order("regular", [{"product_id": "unknown-product", "quantity": 1}])

# Behaviour to preserve 
    def test_order_ids_are_unique(self):
        order1 = self.service.place_order("regular", [{"product_id": "mug", "quantity": 1}])
        order2 = self.service.place_order("regular", [{"product_id": "mug", "quantity": 1}])
        self.assertNotEqual(order1["order_id"], order2["order_id"])

    def test_order_ids_are_sequential(self):
        order1 = self.service.place_order("regular", [{"product_id": "mug", "quantity": 1}])
        order2 = self.service.place_order("regular", [{"product_id": "mug", "quantity": 1}])
        self.assertEqual(order1["order_id"], "ORD-0001")
        self.assertEqual(order2["order_id"], "ORD-0002")

if __name__ == "__main__":
    unittest.main()

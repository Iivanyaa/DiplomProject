import yaml
from django.core.management import BaseCommand
from apps.products.models import Product, Supplier

class Command(BaseCommand):
    help = "Import products from YAML file"

    def add_arguments(self, parser):
        parser.add_argument("file_path", type=str)

    def handle(self, *args, **options):
        with open(options["file_path"]) as f:
            data = yaml.safe_load(f)
            supplier, _ = Supplier.objects.get_or_create(
                name=data["supplier"]["name"],
                defaults={"contact_email": data["supplier"]["email"]}
            )
            
            for product_data in data["products"]:
                Product.objects.update_or_create(
                    supplier=supplier,
                    name=product_data["name"],
                    defaults={
                        "price": product_data["price"],
                        "characteristics": product_data.get("characteristics", {})
                    }
                )
        self.stdout.write("Successfully imported products")
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from services.models import ServiceCategory, Service


# (category_name, [(service_name, price, price_note), ...])
DATA = [
    ("Wash", [
        ("Kids & Teens", 10, ""),
        ("Wash, Conditioning & Blow Dry (Adult)", 25, ""),
        ("Wash Locs (Adult)", 15, ""),
        ("Wash, Conditioning & Blow Dry (Kids & Teens)", 20, ""),
    ]),
    ("Haircut", [
        ("Shape Up (Kids)", 5, ""),
        ("Shape Up (Teens 11-17)", 5, ""),
        ("Shape Up (Adult)", 10, ""),
        ("Haircut (Adult Men)", 20, ""),
        ("Haircut (Ladies)", 15, ""),
    ]),
    ("Locs - Adult", [
        ("Styling", 15, ""),
        ("Interlock/Retwist (Half Head)", 45, ""),
        ("Interlock/Retwist (Full Head)", 55, ""),
        ("Retwist/Interlock + Styling (Half Head)", 55, ""),
        ("Retwist/Interlock + Styling (Full Head)", 65, ""),
        ("Starter Locs (Half Head)", 50, ""),
        ("Starter Locs (Full Head)", 60, ""),
        ("Locs Extensions / Extensive Locs Repairs", 20, "£20 (1st hr), £10/hr after - est. 2hrs"),
        ("Starter Microlocs", 20, "£20 (1st hr), £10/hr after"),
        ("Microlocs Retie (2.5 hrs)", 50, ""),
        ("Microlocs Retie (3.5 hrs)", 65, ""),
        ("Microlocs Retie (4 hrs)", 80, ""),
    ]),
    ("Locs - Teens (13-17)", [
        ("Styling", 10, ""),
        ("Interlock/Retwist (Half Head)", 40, ""),
        ("Interlock/Retwist (Full Head)", 50, ""),
        ("Retwist/Interlock + Styling (Half Head)", 50, ""),
        ("Retwist/Interlock + Styling (Full Head)", 60, ""),
        ("Starter Locs (Half Head)", 45, ""),
        ("Starter Locs (Full Head)", 55, ""),
    ]),
    ("Locs - Kids", [
        ("Styling", 10, ""),
        ("Interlock/Retwist (Half Head)", 35, ""),
        ("Interlock/Retwist (Full Head)", 40, ""),
        ("Retwist/Interlock + Styling (Half Head)", 45, ""),
        ("Retwist/Interlock + Styling (Full Head)", 45, ""),
        ("Starter Locs (Half Head)", 35, ""),
        ("Starter Locs (Full Head)", 45, ""),
    ]),
    ("Professional Removals", [
        ("Cornrow Removal", 30, ""),
        ("Faux Locs Removal", 20, ""),
        ("Combing Out of Locs", 20, "£20/hr"),
    ]),
    ("Kinky Twists", [
        ("Kinky Twists", 60, ""),
    ]),
    ("Cornrows", [
        ("Basic (Half Head)", 30, ""),
        ("Basic (Full Head)", 40, ""),
        ("Stitch Pattern (Half Head)", 50, ""),
        ("Stitch Pattern (Full Head)", 60, ""),
    ]),
    ("Consultations", [
        ("In-Person", 15, ""),
        ("Video Consultation", 10, ""),
    ]),
]


class Command(BaseCommand):
    help = "Seeds ServiceCategory and Service with the real Hair Klinics menu"

    def handle(self, *args, **options):
        for order, (category_name, services) in enumerate(DATA):
            category, created = ServiceCategory.objects.get_or_create(
                slug=slugify(category_name),
                defaults={"name": category_name, "order": order},
            )
            if not created:
                category.name = category_name
                category.order = order
                category.save()

            self.stdout.write(self.style.SUCCESS(
                f"{'Created' if created else 'Updated'} category: {category_name}"
            ))

            for service_name, price, price_note in services:
                service, s_created = Service.objects.update_or_create(
                    category=category,
                    name=service_name,
                    defaults={"price": price, "price_note": price_note, "duration_minutes": 30},  # Default duration set to 30 minutes,
                )
                action = "Created" if s_created else "Updated"
                self.stdout.write(f"  {action} service: {service_name} - £{price}")

        self.stdout.write(self.style.SUCCESS("\nDone seeding services."))
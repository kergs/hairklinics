from django.core.management.base import BaseCommand
from django.utils.text import slugify
from services.models import ServiceCategory, Service

# (service_name, price, price_note, duration_minutes)
# Durations are rough estimates. The client corrects them in the admin.
DATA = [
    ("Wash", [
        ("Kids & Teens", 10, "", 30),
        ("Wash, Conditioning & Blow Dry (Adult)", 25, "", 60),
        ("Wash Locs (Adult)", 15, "", 45),
        ("Wash, Conditioning & Blow Dry (Kids & Teens)", 20, "", 45),
    ]),
    ("Haircut", [
        ("Shape Up (Kids)", 5, "", 15),
        ("Shape Up (Teens 11-17)", 5, "", 15),
        ("Shape Up (Adult)", 10, "", 20),
        ("Haircut (Adult Men)", 20, "", 30),
        ("Haircut (Ladies)", 15, "", 45),
    ]),
    ("Locs - Adult", [
        ("Styling", 15, "", 45),
        ("Interlock/Retwist (Half Head)", 45, "", 90),
        ("Interlock/Retwist (Full Head)", 55, "", 120),
        ("Retwist/Interlock + Styling (Half Head)", 55, "", 120),
        ("Retwist/Interlock + Styling (Full Head)", 65, "", 150),
        ("Starter Locs (Half Head)", 50, "", 150),
        ("Starter Locs (Full Head)", 60, "", 180),
        ("Locs Extensions / Extensive Locs Repairs", 20, "£20 (1st hr), £10/hr after - est. 2hrs", 120),
        ("Starter Microlocs", 20, "£20 (1st hr), £10/hr after", 240),
        ("Microlocs Retie (2.5 hrs)", 50, "", 150),
        ("Microlocs Retie (3.5 hrs)", 65, "", 210),
        ("Microlocs Retie (4 hrs)", 80, "", 240),
    ]),
    ("Locs - Teens (13-17)", [
        ("Styling", 10, "", 30),
        ("Interlock/Retwist (Half Head)", 40, "", 75),
        ("Interlock/Retwist (Full Head)", 50, "", 105),
        ("Retwist/Interlock + Styling (Half Head)", 50, "", 105),
        ("Retwist/Interlock + Styling (Full Head)", 60, "", 135),
        ("Starter Locs (Half Head)", 45, "", 120),
        ("Starter Locs (Full Head)", 55, "", 150),
    ]),
    ("Locs - Kids", [
        ("Styling", 10, "", 30),
        ("Interlock/Retwist (Half Head)", 35, "", 60),
        ("Interlock/Retwist (Full Head)", 40, "", 90),
        ("Retwist/Interlock + Styling (Half Head)", 45, "", 90),
        ("Retwist/Interlock + Styling (Full Head)", 45, "", 105),
        ("Starter Locs (Half Head)", 35, "", 90),
        ("Starter Locs (Full Head)", 45, "", 120),
    ]),
    ("Professional Removals", [
        ("Cornrow Removal", 30, "", 60),
        ("Faux Locs Removal", 20, "", 90),
        ("Combing Out of Locs", 20, "£20/hr", 60),
    ]),
    ("Kinky Twists", [
        ("Kinky Twists", 60, "", 240),
    ]),
    ("Cornrows", [
        ("Basic (Half Head)", 30, "", 60),
        ("Basic (Full Head)", 40, "", 90),
        ("Stitch Pattern (Half Head)", 50, "", 90),
        ("Stitch Pattern (Full Head)", 60, "", 120),
    ]),
    ("Consultations", [
        ("In-Person", 15, "", 30),
        ("Video Consultation", 10, "", 20),
    ]),
]


class Command(BaseCommand):
    help = "Seeds the Hair Klinics menu. Existing services are left alone unless --update-durations is used."

    def add_arguments(self, parser):
        parser.add_argument(
            '--update-durations',
            action='store_true',
            help='Also overwrite duration_minutes on services that already exist',
        )

    def handle(self, *args, **options):
        update_durations = options['update_durations']

        for order, (category_name, services) in enumerate(DATA):
            category, _ = ServiceCategory.objects.get_or_create(
                slug=slugify(category_name),
                defaults={"name": category_name, "order": order},
            )

            for name, price, note, minutes in services:
                service, created = Service.objects.get_or_create(
                    category=category,
                    name=name,
                    defaults={"price": price, "price_note": note, "duration_minutes": minutes},
                )
                if created:
                    self.stdout.write(f"Created: {category_name} / {name}")
                elif update_durations and service.duration_minutes != minutes:
                    service.duration_minutes = minutes
                    service.save(update_fields=['duration_minutes'])
                    self.stdout.write(f"Updated duration: {name} -> {minutes} min")

        self.stdout.write(self.style.SUCCESS("Done seeding services."))
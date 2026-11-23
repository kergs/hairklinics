from django.core.management.base import BaseCommand
from django.utils.text import slugify
from services.models import ServiceCategory, Service

# (category_name, default_duration_minutes, [(service_name, price, price_note[, duration_override]), ...])
# Durations come from the client. The client can still edit them in the admin.
DATA = [
    ("Wash", 15, [
        ("Kids & Teens", 10, ""),
        ("Wash, Conditioning & Blow Dry (Adult)", 25, ""),
        ("Wash Locs (Adult)", 15, ""),
        ("Wash, Conditioning & Blow Dry (Kids & Teens)", 20, ""),
    ]),
    ("Haircut", 30, [
        ("Shape Up (Kids)", 5, ""),
        ("Shape Up (Teens 11-17)", 5, ""),
        ("Shape Up (Adult)", 10, ""),
        ("Haircut (Adult Men)", 20, ""),
        ("Haircut (Ladies)", 15, ""),
    ]),
    ("Locs - Adult", 150, [
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
        ("Microlocs Retie (3.5 hrs)", 65, "", 210),
        ("Microlocs Retie (4 hrs)", 80, "", 240),
    ]),
    ("Locs - Teens (13-17)", 120, [
        ("Styling", 10, ""),
        ("Interlock/Retwist (Half Head)", 40, ""),
        ("Interlock/Retwist (Full Head)", 50, ""),
        ("Retwist/Interlock + Styling (Half Head)", 50, ""),
        ("Retwist/Interlock + Styling (Full Head)", 60, ""),
        ("Starter Locs (Half Head)", 45, ""),
        ("Starter Locs (Full Head)", 55, ""),
    ]),
    ("Locs - Kids", 120, [
        ("Styling", 10, ""),
        ("Interlock/Retwist (Half Head)", 35, ""),
        ("Interlock/Retwist (Full Head)", 40, ""),
        ("Retwist/Interlock + Styling (Half Head)", 45, ""),
        ("Retwist/Interlock + Styling (Full Head)", 45, ""),
        ("Starter Locs (Half Head)", 35, ""),
        ("Starter Locs (Full Head)", 45, ""),
    ]),
    ("Professional Removals", 120, [
        ("Cornrow Removal", 30, ""),
        ("Faux Locs Removal", 20, ""),
        ("Combing Out of Locs", 20, "£20/hr"),
    ]),
    ("Kinky Twists", 150, [
        ("Kinky Twists", 60, ""),
    ]),
    ("Cornrows", 120, [
        ("Basic (Half Head)", 30, ""),
        ("Basic (Full Head)", 40, ""),
        ("Stitch Pattern (Half Head)", 50, ""),
        ("Stitch Pattern (Full Head)", 60, ""),
    ]),
    ("Consultations", 30, [
        ("In-Person", 15, ""),
        ("Video Consultation", 10, ""),
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

        for order, (category_name, default_minutes, services) in enumerate(DATA):
            category, _ = ServiceCategory.objects.get_or_create(
                slug=slugify(category_name),
                defaults={"name": category_name, "order": order},
            )

            for item in services:
                name, price, note = item[0], item[1], item[2]
                minutes = item[3] if len(item) > 3 else default_minutes

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
                    self.stdout.write(f"Updated duration: {category_name} / {name} -> {minutes} min")

        self.stdout.write(self.style.SUCCESS("Done seeding services."))
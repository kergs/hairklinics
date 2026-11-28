from datetime import time

from django.core.management.base import BaseCommand

from bookings.models import TimeBlock
from services.models import ServiceCategory

BLOCKS = [
    (time(9, 0), time(11, 30)),
    (time(11, 30), time(13, 0)),
    (time(13, 0), time(15, 30)),
    (time(15, 30), time(18, 0)),
    (time(18, 0), time(20, 0)),
]


class Command(BaseCommand):
    help = "First-run setup: creates the Locs time blocks and switches the Locs categories to fixed blocks."

    def handle(self, *args, **options):
        if TimeBlock.objects.exists():
            self.stdout.write("Time blocks already exist; leaving them alone.")
            return

        for start, end in BLOCKS:
            TimeBlock.objects.create(start_time=start, end_time=end)

        updated = ServiceCategory.objects.filter(name__startswith='Locs').update(
            booking_mode=ServiceCategory.MODE_BLOCKS
        )
        self.stdout.write(self.style.SUCCESS(
            f"Created {len(BLOCKS)} time blocks; set {updated} Locs categories to fixed blocks."
        ))
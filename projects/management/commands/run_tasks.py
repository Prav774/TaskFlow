from django.core.management.base import BaseCommand
from projects.tasks import check_auto_approval, check_overdue_segments, check_abandoned_segments


class Command(BaseCommand):
    help = 'Run scheduled tasks (auto-approval, overdue check, abandoned check)'

    def handle(self, *args, **options):
        self.stdout.write('Running scheduled tasks...')
        
        check_auto_approval()
        self.stdout.write(self.style.SUCCESS('✓ Auto-approval check completed'))
        
        check_overdue_segments()
        self.stdout.write(self.style.SUCCESS('✓ Overdue segments check completed'))
        
        check_abandoned_segments()
        self.stdout.write(self.style.SUCCESS('✓ Abandoned segments check completed'))
        
        self.stdout.write(self.style.SUCCESS('All tasks completed!'))

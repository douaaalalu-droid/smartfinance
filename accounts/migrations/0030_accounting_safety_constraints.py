from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0029_exchangerate_updated_at'),   
    ]

    operations = [

        migrations.AddConstraint(
            model_name='invoice',
            constraint=models.CheckConstraint(
                condition=Q(total_amount__gte=0),
                name='invoice_total_positive'
            ),
        ),

        migrations.AddConstraint(
            model_name='journalentryline',
            constraint=models.CheckConstraint(
                condition=Q(debit__gte=0),
                name='debit_positive'
            ),
        ),

        migrations.AddConstraint(
            model_name='journalentryline',
            constraint=models.CheckConstraint(
                condition=Q(credit__gte=0),
                name='credit_positive'
            ),
        ),

    ]
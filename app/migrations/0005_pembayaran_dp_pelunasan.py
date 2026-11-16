from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0004_article_deskripsi_seo_category_status_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='total_harga',
            field=models.PositiveIntegerField(
                default=0, help_text='Harga paket saat booking dibuat (0 = pakai harga paket sekarang)'),
        ),
        migrations.AddField(
            model_name='payment',
            name='jenis',
            field=models.CharField(
                choices=[('dp', 'DP'), ('full', 'Bayar Penuh'), ('pelunasan', 'Pelunasan')],
                default='dp', max_length=10),
        ),
        migrations.AddField(
            model_name='payment',
            name='snap_token',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='websetting',
            name='nominal_dp',
            field=models.PositiveIntegerField(default=50000, verbose_name='Nominal DP booking (Rp)'),
        ),
    ]
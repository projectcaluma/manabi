from django.db import models


class Lock(models.Model):
    token = models.CharField(max_length=128, primary_key=True)
    data = models.JSONField()

    class Meta:
        db_table = "manabi_lock"

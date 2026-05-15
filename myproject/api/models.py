from django.db import models

class Sign(models.Model):
    label = models.CharField(max_length=100, db_index=True)
    hand = models.CharField(max_length=10, choices=[('left','left'),('right','right')], default='right')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.label

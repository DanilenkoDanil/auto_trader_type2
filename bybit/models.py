from django.db import models
from django.template.defaultfilters import default


class Trader(models.Model):
    username = models.CharField(max_length=10)
    api_key = models.CharField(max_length=30)
    api_secret = models.CharField(max_length=45)
    balance = models.DecimalField(decimal_places=8, max_digits=20)
    settings = models.ForeignKey("Settings", on_delete=models.PROTECT, related_name="settings")

    def __str__(self):
        return f"Username {self.username}"


class GlobalSetting(models.Model):
    switch_rejection = models.FloatField(default=10)
    reaction = models.BooleanField(default=True)

class Settings(models.Model):
    stop_loss_percent = models.FloatField()
    take_profit_percent = models.FloatField()
    leverage = models.FloatField()
    amount_usd = models.FloatField()
    demo = models.BooleanField(default=False)
    close_by_picture = models.BooleanField(default=True)
    close_by_stop = models.BooleanField(default=True)


    def __str__(self):
        trader = self.settings.first()
        if trader:
            return f"Setting for {trader.username}"
        return f"Setting {self.id}"

    class Meta:
        verbose_name = "Settings"
        verbose_name_plural = "Settings"


class Chat(models.Model):
    name = models.CharField(max_length=80)
    chat_id = models.CharField(max_length=80)

    def __str__(self):
        return f"Chat {self.name}"


class EntryPrice(models.Model):
    symbol = models.CharField(max_length=20)
    side = models.CharField(max_length=4)
    entry_price = models.FloatField()
    first_target_price = models.FloatField(default=0)
    timestamp = models.DateTimeField(auto_now_add=True)


class ErrorLog(models.Model):
    error = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    symbol = models.CharField(max_length=10)


from main.models import experiment_session_days

esds = experiment_session_days.objects.filter(paypal_api = True, paypal_api_batch_id="").order_by('id')

for i in esds:
    i.updatePayPalBatchIDFromMemo()

exit()
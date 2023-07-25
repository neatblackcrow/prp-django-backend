from django.db import models
from datetime import datetime

class NeuralNetworkWeight(models.Model):
    weight = models.FloatField(db_column='weight')

    class Meta:
        db_table = 'neural_network_weight'

class UserCase(models.Model):
    createdOn = models.DateTimeField(db_column='created_on', primary_key=True, default=datetime.now)

    lastPredictedInterval = models.FloatField(db_column='last_predicted_interval')
    reviewInterval = models.FloatField(db_column='review_interval')
    repetition = models.FloatField(db_column='repetition')
    grade = models.FloatField(db_column='grade')
    predictedInterval = models.FloatField(db_column='predicted_interval')

    class Meta:
        db_table = 'user_case'
        constraints = [
            models.CheckConstraint(check = models.Q(lastPredictedInterval__gte = 0.0) & models.Q(lastPredictedInterval__lte = 1.0), name='lastPredictedInterval range'),
            models.CheckConstraint(check = models.Q(reviewInterval__gte = 0.0) & models.Q(reviewInterval__lte = 1.0), name='reviewInterval range'),
            models.CheckConstraint(check = models.Q(repetition__gte = 0.0) & models.Q(repetition__lte = 1.0), name='repetition range'),
            models.CheckConstraint(check = models.Q(grade__gte = 0.0) & models.Q(grade__lte = 1.0), name='grade range'),
            models.CheckConstraint(check = models.Q(predictedInterval__gte = 0.0) & models.Q(predictedInterval__lte = 1.0), name='predictedInterval range'),
        ]

class CardType(models.Model):
    name = models.TextField(db_column='name', primary_key=True, max_length=100)

    class Meta:
        db_table = 'card_type'

class Category(models.Model):
    name = models.TextField(db_column='name')
    createdOn = models.DateTimeField(db_column='created_on', default=datetime.now)
    updatedOn = models.DateTimeField(db_column='updated_on', default=datetime.now)
    parentCategory = models.ForeignKey(db_column='parent_category', to='Category', on_delete=models.PROTECT, default=1)
    ordered = models.IntegerField(db_column='ordered')

    class Meta:
        db_table = 'category'
        constraints = [
            models.CheckConstraint(check=models.Q(updatedOn__gte=models.F('createdOn')), name='updatedOn_gte_createdOn'),
            models.CheckConstraint(check=models.Q(ordered__gt=0), name='ordered_gt_0'),
        ]

class Card(models.Model):
    createdOn = models.DateTimeField(db_column='created_on', default=datetime.now)
    updatedOn = models.DateTimeField(db_column='updated_on', default=datetime.now)

    lastPredictedInterval = models.IntegerField(db_column='last_predicted_interval')
    reviewInterval = models.IntegerField(db_column='review_interval')
    repetition = models.IntegerField(db_column='repetition')
    grade = models.IntegerField(db_column='grade')
    predictedInterval = models.IntegerField(db_column='predicted_interval')

    front = models.TextField(db_column='front')
    back = models.TextField(db_column='back', null=True)
    nextReviewOn = models.DateField(db_column='next_review_on')
    lastReviewOn = models.DateField(db_column='last_review_on', default=datetime.now)
    category = models.ForeignKey(db_column='category', to='Category', on_delete=models.PROTECT, default=1)
    cardType = models.ForeignKey(db_column='card_type', to='CardType', on_delete=models.PROTECT)
    ordered = models.IntegerField(db_column='ordered')

    class Meta:
        db_table = 'card'
        constraints = [
            models.CheckConstraint(check = models.Q(lastPredictedInterval__gte = 0) & models.Q(lastPredictedInterval__lte = 2048), name='lastPredictedInterval range card'),
            models.CheckConstraint(check = models.Q(reviewInterval__gte = 0) & models.Q(reviewInterval__lte = 2048), name='review range card'),
            models.CheckConstraint(check = models.Q(repetition__gte = 0) & models.Q(repetition__lte = 128), name='repetition range card'),
            models.CheckConstraint(check = models.Q(grade__gte = 0) & models.Q(grade__lte = 5), name='grade range card'),
            models.CheckConstraint(check = models.Q(predictedInterval__gte = 0) & models.Q(predictedInterval__lte = 2048), name='predictedInterval range cared'),
            models.CheckConstraint(check = models.Q(updatedOn__gte=models.F('createdOn')), name='updatedOn_gte_createdOn card'),
            models.CheckConstraint(check = models.Q(ordered__gt=0), name='ordered_gt_0 card'),
        ]
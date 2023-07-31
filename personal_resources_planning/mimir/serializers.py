from rest_framework import serializers
from mimir.models import Category, Card, CardType

class CardSerializer(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(read_only=True)
    createdOn = serializers.DateTimeField(read_only=True)
    updatedOn = serializers.DateTimeField(read_only=True)

    lastPredictedInterval = serializers.IntegerField(read_only=True)
    reviewInterval = serializers.IntegerField(read_only=True)
    repetition = serializers.IntegerField(read_only=True)
    predictedInterval = serializers.IntegerField(read_only=True)

    nextReviewOn = serializers.DateField(read_only=True)
    lastReviewOn = serializers.DateField(read_only=True)

    front = serializers.CharField(min_length=1, max_length=2000, trim_whitespace=True, allow_blank=False)
    back = serializers.CharField(required=False, min_length=1, max_length=2000, trim_whitespace=True, allow_blank=True)
    grade = serializers.IntegerField(min_value=0, max_value=5, default=0)

    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())
    cardType = serializers.PrimaryKeyRelatedField(queryset=CardType.objects.all())
    ordered = serializers.IntegerField(min_value=1)

    def create(self, validated_data):
        return Card.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.updatedOn = validated_data.get('updatedOn')
        instance.front = validated_data.get('front', instance.front)
        instance.back = validated_data.get('back', instance.back)
        instance.grade = validated_data.get('grade', instance.grade)
        instance.category = validated_data.get('category', instance.category)
        instance.cardType = validated_data.get('cardType', instance.cardType)
        instance.ordered = validated_data.get('ordered', instance.ordered)
        instance.save()
        return instance
    
class CategorySerializer(serializers.ModelSerializer):

    cards = CardSerializer(many=True)

    def to_representation(self, instance):
        if instance.id > 0:
            self.fields['children'] = CategorySerializer(many=True, read_only=True)
        return super(CategorySerializer, self).to_representation(instance)

    class Meta:
        model = Category
        fields = ['id', 'name', 'createdOn', 'updatedOn', 'parentCategory', 'ordered', 'cards']
        read_only_fields = ['id', 'createdOn', 'updatedOn']
    
class ReviewSerializer(serializers.Serializer):
    cardId = serializers.IntegerField(min_value=1)
    actualGrade = serializers.IntegerField(min_value=0, max_value=5)
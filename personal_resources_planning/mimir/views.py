from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from mimir.neural_network import NeuralNetwork
from mimir.serializers import CardSerializer, CategorySerializer
from mimir.models import Card, Category
from datetime import datetime, timedelta

# Create your views here.
nn = NeuralNetwork()

@api_view(['GET'])
def buildKnowledgeTree(request):
    pass

@api_view(['POST'])
def createCard(request):
    serializer = CardSerializer(data=request.data)
    if serializer.is_valid():
        predictedInterval = nn.predictNextInterval(0, 0, 0, 0) # Default grade is 0
        serializer.save(lastPredictedInterval=0,
                        reviewInterval=0,
                        repetition=0,
                        predictedInterval=predictedInterval,
                        nextReviewOn=(datetime.now() + timedelta(days=predictedInterval)).date())
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT', 'DELETE'])
def updateOrDeleteCard(request, card_id):
    try:
        card = Card.objects.get(id=card_id)
    except Card.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'PUT':
        serializer = CardSerializer(card, data=request.data)
        if serializer.is_valid():
            serializer.save(updatedOn=datetime.now())
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    elif request.method == 'DELETE':
        card.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['POST'])
def createCategory(request):
    serializer = CategorySerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

def _removeSubCategoryRecursively(category_id):
    effectedCategories = Category.objects.filter(parentCategory=category_id)

    for category in effectedCategories:
        _removeSubCategoryRecursively(category.id)

        effectedCards = Card.objects.filter(category=category.id)
        for card in effectedCards:
            card.delete()

        category.delete()

@api_view(['PUT', 'DELETE'])
def updateOrDeleteCategory(request, category_id):
    try:
        category = Category.objects.get(id=category_id)
    except Category.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'PUT':
        serializer = CategorySerializer(category, data=request.data)
        if serializer.is_valid():
            serializer.save(updatedOn=datetime.now())
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    elif request.method == 'DELETE':
        # must warn user about deleting all cateories or cards that under this category.
        # Remove subcategory recursively along side their cards.
        _removeSubCategoryRecursively(category_id)

        # Remove current category's cards
        Card.objects.filter(category=category_id).delete()
        
        # Then remove the category itself.
        category.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['POST'])
def reviewCard(request):
    pass
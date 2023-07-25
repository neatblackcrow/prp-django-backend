from django.shortcuts import render
from django.http import HttpResponse
from .neural_network import NeuralNetwork

# Create your views here.
nn = NeuralNetwork()

def index(request):
    print(nn.predictNextInterval(1, 1, 1, 3))
    return HttpResponse('test')
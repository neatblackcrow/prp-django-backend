import math
import numpy as np
from numpy.random import shuffle
from django.db import transaction
from .models import NeuralNetworkWeight, UserCase


class NeuralNetwork:

    def __init__(self):
        self._maxRepetition = 128.0
        self._maxInterval = 2048.0
        self._maxGrade = 5.0

        self._normalizeRepetition = lambda repetition: repetition / self._maxRepetition
        self._normalizeInterval = lambda day: math.sqrt(day / self._maxInterval)
        self._normalizeGrade = lambda grade: grade / self._maxGrade
        self._deNormalizeInterval = lambda day: round(math.pow(day, 2) * self._maxInterval)

        self._userCases: np.ndarray

        self._network = [NeuralNetwork.Layer(4), NeuralNetwork.Layer(20), NeuralNetwork.Layer(1)]
        self._sigmoid = lambda x: 1.0 / (1.0 + math.pow(math.e, -x))
        self._sigmoidDerivative = lambda y: y * (1.0 - y)
        self._rootedMeanSquaredError = lambda errors: math.sqrt(sum([math.pow(e, 2) for e in errors]) / len(errors))

        self.latestLearningRate = 0.1
        self.latestRMSE = 0.0
        self.totalSessionEpochs = 0

        self._restoreWeights()
        self._restoreUserCases()

    class Layer:
        def __init__(self, units):
            self.units = units
            self.weights = np.zeros((units, 20))
            self.outputs = np.zeros(units)
            self.errors = np.zeros(units)

    def _restoreWeights(self):
        weights = [i.weight for i in NeuralNetworkWeight.objects.all()]
        counter = 0
        for l in range(1, len(self._network)):
            for w in range(0, self._network[l].units):
                self._network[l].weights[w][0:self._network[l - 1].units] = weights[counter:counter + self._network[l - 1].units]
                counter += self._network[l - 1].units

    def _restoreUserCases(self):
        userCases = UserCase.objects.order_by('-createdOn')[:101]
        cases = []
        for case in userCases:
            duplicateCase = [c for c in cases
                       if c[0] == case.lastPredictedInterval and
                       c[1] == case.reviewInterval and
                       c[2] == case.repetition and
                       c[3] == case.grade]
            if duplicateCase == []:
                cases.append([case.lastPredictedInterval, case.reviewInterval, case.repetition, case.grade, case.predictedInterval])
            else:
                duplicateCase[0][4] = (duplicateCase[0][4] + case.predictedInterval) / 2
        self._userCases = np.array(cases)

    @transaction.atomic
    def _saveWeights(self):
        pk = 1
        for l in range(1, len(self._network)):
            for w in range(0, self._network[l].units):
                for i in range(0, self._network[l - 1].units):
                    NeuralNetworkWeight.objects.filter(id = pk).update(weight = self._network[l].weights[w][i])
                    pk += 1
    
    def _saveUserCase(self, lastPredictedInterval, reviewInterval, repetition, grade, betterInterval):
        UserCase.objects.create(
            lastPredictedInterval = self._normalizeInterval(lastPredictedInterval),
            reviewInterval = self._normalizeInterval(reviewInterval),
            repetition = self._normalizeRepetition(repetition),
            grade = self._normalizeGrade(grade),
            predictedInterval = self._normalizeInterval(betterInterval))

    def _propagation(self, lastPredictedInterval, reviewInterval, repetition, grade):
        self._network[0].outputs[0] = lastPredictedInterval
        self._network[0].outputs[1] = reviewInterval
        self._network[0].outputs[2] = repetition
        self._network[0].outputs[3] = grade

        for l in range(0, len(self._network) - 1):
            for i in range(0, self._network[l + 1].units):
                sum = 0.0

                for j in range(0, self._network[l].units):
                    sum += self._network[l + 1].weights[i][j] * self._network[l].outputs[j]

                self._network[l + 1].outputs[i] = self._sigmoid(sum)

        return self._network[-1].outputs[0]

    def predictNextInterval(self, predictedInterval, reviewInterval, repetition, grade):
        return self._deNormalizeInterval(
            self._propagation(
                self._normalizeInterval(predictedInterval),
                self._normalizeInterval(reviewInterval),
                self._normalizeRepetition(repetition),
                self._normalizeGrade(grade)
            )
        )

    def feedBackToNeuralNetwork(self,
                                lastPredictedInterval,
                                reviewInterval,
                                repetition,
                                grade,
                                predictedInterval,
                                actualInterval,
                                actualGrade):
        betterInterval = actualInterval
        factor = 0.0
        match actualGrade:
            case 0:
                if actualInterval > predictedInterval:
                    betterInterval = (actualInterval + predictedInterval) / 2
                factor = 0.4
            case 1:
                if actualInterval > predictedInterval:
                    betterInterval = (actualInterval + predictedInterval) / 2
                factor = 0.55
            case 2:
                if actualInterval > predictedInterval:
                    betterInterval = (actualInterval + predictedInterval) / 2
                factor = 0.7
            case 3:
                if actualInterval > predictedInterval:
                    betterInterval = (actualInterval + predictedInterval) / 2
                factor = 0.85
            case 4:
                factor = 1.0
            case 5:
                if actualInterval < predictedInterval:
                    betterInterval = (actualInterval + predictedInterval) / 2
                factor = 1.2
            case _:
                factor = 0.0

        betterInterval *= factor

        self._userCases = np.append(self._userCases, [[
            self._normalizeInterval(lastPredictedInterval),
            self._normalizeInterval(reviewInterval),
            self._normalizeRepetition(repetition),
            self._normalizeGrade(grade),
            self._normalizeInterval(betterInterval)
        ]], axis = 0)
        self._saveUserCase(lastPredictedInterval, reviewInterval, repetition, grade, betterInterval)

        self._userCases = np.delete(self._userCases, 0, axis = 0)

        self._onlineTraining()


    def _backPropagation(self, expectedInterval):
        networkOutput = self._network[2].outputs[0]
        networkError = networkOutput - expectedInterval
        self._network[2].errors[0] = self._sigmoidDerivative(networkOutput) * networkError

        for l in range(len(self._network) - 1, 1, -1):
            for i in range(0, self._network[l - 1].units):
                output = self._network[l - 1].outputs[i]
                error = 0.0

                for j in range(0, self._network[l].units):
                    error += self._network[l].weights[j][i] * self._network[l].errors[j]

                self._network[l - 1].errors[i] = self._sigmoidDerivative(output) * error

        return networkError

    def _simulateNeuralNetwork(self,
                               lastPredictedInterval,
                               reviewInterval,
                               repetition,
                               grade,
                               predictedInterval):
        self._propagation(lastPredictedInterval, reviewInterval, repetition, grade)
        networkError = self._backPropagation(predictedInterval)

        for l in range(1, len(self._network)):
            for i in range(0, self._network[l].units):
                for j in range(0, self._network[l - 1].units):
                    self._network[l].weights[i][j] -= \
                    self._network[l].errors[i] * self._network[l - 1].outputs[j] * self.latestLearningRate
        
        return networkError

    def _onlineTraining(self, epochFactor = 8, targetRMSE = 0.0125):
        if self._userCases.size == 0:
            return
        
        totalEpochs = epochFactor * self._userCases.size
        epochCounter = 1

        while True:
            networkErrors = []

            for case in self._userCases:
                networkErrors.append(self._simulateNeuralNetwork(case[0], case[1], case[2], case[3], case[4]))

            self.latestRMSE = self._rootedMeanSquaredError(networkErrors)
            self.latestLearningRate = 0.9 if self.latestRMSE >= 0.02 else 0.1
            self.totalSessionEpochs += 1

            shuffle(self._userCases)

            if epochCounter == totalEpochs or self.latestRMSE <= targetRMSE:
                break
            
            epochCounter += 1

        self._saveWeights()
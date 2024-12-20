
from django.test import TransactionTestCase
from django.db.models import Avg, Max, F
from django.db.models.functions import Cast
from django.db.models import FloatField
from .models import Course, ResultatCourse, Coureur
from django.db import connection


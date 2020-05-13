'''
Created on Feb 12, 2020

@author: Tim Kreuzer
'''

from flask_restful import Resource

class HealthHandler(Resource):
    def get(self):
        return '', 200

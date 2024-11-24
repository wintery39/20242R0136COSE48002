#!/usr/bin/env python
# coding: utf-8
# %%
from flask import Flask, request
from flask_restx import Resource, Namespace, fields
from tasks import rev_generate
import torch

@RV.route('')
class RVResource(Resource):
    @RV.expect(RV_fields)
    def post(self):
        request_data = request.json
        context = request_data["context"]
        
        
        modeloutput = rev_generate.delay(request_data)

        return {"outputid": modeloutput.id}

# %%

from flask import Flask, request, jsonify
from flask_restx import Resource, Namespace, fields, reqparse
from tasks import change, capp
from celery.result import AsyncResult

etc = Namespace(name='etc', description='기타 등등')

etc_fields = etc.model('etc', {
    'company' : fields.String(required=True, description='The company', example='회사명'),
    'field' : fields.String(required=True, description='The field', example='식품'),
    'team' : fields.String(required=True, description='The team', example='조직명')
})


@etc.route('/choice/<string:type>')
class etcGet(Resource):
    def get(self, type):
        if type is None:
            return {"message": "type이 없습니다"}
        available_type = ["llama", "polyglot","gemma"]
        if type in available_type:
            result = change.delay(type)
            return {"message": result.id}
        else:
            return {"message": "오류가 발생했습니다"}        


@etc.route('/result/<string:output_id>')
class etcGetResult(Resource):
    def get(self, output_id):
        if output_id is None:
            return {"status": "error",
            "message": "output_id가 없습니다",
            "output": None
            }
        try:
            output = AsyncResult(output_id, app=capp)
        except Exception as e:
            return {"status": "error", 
            "message": str(e), 
            "output": None
            }  
        if output.ready():
            return {"status": output.state, 
            "message": None} | output.get()
        else:
            return {"status": output.state, 
            "message": None,
            "output": None}


# @etc.route('/info')
# class etcPostInfo(Resource):
#     @etc.expect(etc_fields)
#     def post(self):
#         request_data = request.json
#         result = company_obj_kr(request_data)
#         return result

from flask import Flask, request, jsonify
from flask_restx import Resource, Namespace, fields, reqparse
from repo import get_okr_with_company, findByNum
from tasks import eval_generate
import os

okr = Namespace(name='okr', description='OKR 조회')
okr_parser = reqparse.RequestParser()
okr_parser.add_argument('company_name',  type=str, default=None, required=False, help='The company name')
okr_fields = okr.model('okr', {
    'okrNums': fields.List(fields.Integer, required=True, description="List of okrNum", example=[1, 2, 3]),
})
file_upload = okr.model('FileUpload', {
    'file': fields.Raw(required=True, description='The file to upload', type='file')
})

@okr.route('/')
class okrGet(Resource):
    @okr.expect(okr_parser)
    def get(self):
        args = okr_parser.parse_args()
        company_name = args.get('company_name')
        return jsonify(get_okr_with_company(company_name))

@okr.route('/ai/')
class okrai(Resource):
    @okr.expect(okr_parser)
    def get(self):
        args = okr_parser.parse_args()
        company_name = args.get('company_name')
        return jsonify(get_okr_with_company(company_name, prediction=True))

    @okr.expect(okr_fields)
    def post(self):
        request_data = request.json
        output = []

        keys = ['predict1', 'predict2', 'predict3', 'okrNum']

        for okr_num in request_data["okrNums"]:
            info = findByNum(okr_num)

            temp_dict = dict.fromkeys(keys)
            if info == None:
                temp_dict = {key: "Error" for key in keys[:-1]}
            else:
                if info["isObjective"] == True:
                    for i, key in enumerate(keys[:-2]):
                        temp_dict[key] = eval_generate.delay(info, i).id
                else:
                    for i, key in enumerate(keys[:-1]):
                        temp_dict[key] = eval_generate.delay(info, i).id
            temp_dict['okrNum'] = okr_num
            output.append(temp_dict)
        
        return jsonify(output)

@okr.route('/file/')
class okrfile(Resource):
    @okr.doc('upload_file')
    @okr.expect(file_upload)
    def post(self):
        if 'file' not in request.files:
            return {'message': 'No file part'}, 400
        file = request.files['file']

        if file.filename == '':
            return {'message': 'No selected file'}, 400

        if file and '.xlsx' in filename:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return {'message': 'File uploaded successfully', 'filename': filename}, 201
        else:
            return {'message': 'File type not allowed'}, 400
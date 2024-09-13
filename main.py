from flask import Flask, render_template, request, jsonify, Response, url_for
from flask_restful import Api, Resource
from flasgger import Swagger
import report_racers
from db import db, DriverModel, StartLogModel, EndLogModel
import xml.etree.ElementTree as ET

app = Flask(__name__)
api = Api(app)
swagger = Swagger(app)

db.create_tables([DriverModel, StartLogModel, EndLogModel], safe=True)
report_racers.store_data_from_files_to_db()
report_racers.result_update()


@app.route('/report')
def index():
    '''This route handles the main page'''
    order = request.args.get('order', 'asc')
    sorted_data = report_racers.get_all_racer(order)
    return render_template('index.html', report=sorted_data)


@app.route('/report/drivers/')
def info_in_drivers():
    '''shows a list of driver's names and codes. The code should be a link to info about drivers'''
    order = request.args.get('order', 'asc')
    sorted_data = report_racers.get_all_racer(order)
    return render_template('info_in_drivers.html', report=sorted_data)


@app.route('/report/drivers/<name>')
def name_page(name):
    '''Returns a page with the name'''
    order = request.args.get('order', 'asc')
    sorted_data = report_racers.get_all_racer(order)
    found_item = next(item for item in sorted_data if item['code'] == name)
    return render_template('name_page.html', racer=found_item)


class RenderXML:

    @staticmethod
    def dictxml(data):

        root = ET.Element('drivers')
        for racer in data:
            driver_element = ET.SubElement(root, 'driver')
            ET.SubElement(driver_element, 'time').text = racer['result_time']
            data_element = ET.SubElement(driver_element, 'data')
            ET.SubElement(data_element, 'code').text = racer['code']
            ET.SubElement(data_element, 'name').text = racer['name']
            ET.SubElement(data_element, 'team').text = racer['team']
        return ET.tostring(root, encoding='utf-8', method='xml')

    def render(self, data):
        return Response(self.dictxml(data), mimetype='text/xml')


class RenderJson:

    @staticmethod
    def render(data):
        return data


class RenderMixin:
    renders = {
        "json": RenderJson,
        "xml": RenderXML
    }

    def render(self, data, format="json"):

        render_ = self.renders.get(format)
        if not render_:
            raise ValueError(
                f"Format does not support. Support formats are {
                    self.renders}")
        return render_().render(data)


class IndexApi(Resource, RenderMixin):
    """
    API resource for retrieving and rendering a sorted list of racers.

    Methods:
        get():
            Retrieves the list of racers, sorts them according to the specified order,
            and renders the list in the specified format.

    Query Parameters:
        order (str): Specifies the order of sorting ('asc' for ascending, 'desc' for descending).
                     Defaults to 'asc'.
        format (str): Specifies the format of the response ('json' or other formats supported by render method).
                      Defaults to 'json'.
    """

    def get(self):
        order = request.args.get('order', 'asc')
        format_param = request.args.get('format', 'json')
        sorted_data = report_racers.get_all_racer(order)
        return self.render(sorted_data, format_param)


class InfoDriver(Resource, RenderMixin):
    """
    API resource for retrieving and rendering detailed information about drivers.

    Methods:
        get():
            Retrieves the detailed information of drivers, sorts them according to the specified order,
            and renders the information in the specified format with URLs for each driver's detailed page.

    Query Parameters:
        order (str): Specifies the order of sorting ('asc' for ascending, 'desc' for descending).
                     Defaults to 'asc'.
        format (str): Specifies the format of the response ('json' or other formats supported by render method).
                      Defaults to 'json'.
    """

    def get(self):
        order = request.args.get('order', 'asc')
        format_param = request.args.get('format', 'json')
        sorted_data_info = report_racers.get_all_racer(order)
        for racer in sorted_data_info:
            racer['code'] = (
                url_for(
                    'namepage',
                    name=racer['code'],
                    _external=True))
        return self.render(sorted_data_info, format_param)


class NamePage(Resource, RenderMixin):
    """
    API resource for retrieving and rendering information about a specific racer.

    Methods:
        get(name):
            Retrieves the information of a racer specified by their code and renders it in the specified format.

    Path Parameters:
        name (str): The code of the racer to retrieve information for.

    Query Parameters:
        format (str): Specifies the format of the response ('json' or other formats supported by render method).
                      Defaults to 'json'.
    """

    def get(self, name):
        format_param = request.args.get('format', 'json')
        page = report_racers.get_racer_by_code(name)
        return self.render(page, format_param)


api.add_resource(InfoDriver, '/api/v1/report/drivers/')
api.add_resource(IndexApi, '/api/v1/report/')
api.add_resource(NamePage, '/api/v1/report/drivers/<name>/')

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)

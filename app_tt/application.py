from flask import render_template, request, url_for
from engine.api import blueprint as api
from meb.collaborate import blueprint as collaborate
from meb.util import crossdomain
from administration.admin import blueprint as admin
from meb_results.results import blueprint as results
from core import app

app.register_blueprint(collaborate, url_prefix='/collaborate')
app.register_blueprint(api, url_prefix='/api')
app.register_blueprint(admin, url_prefix='/admin')
app.register_blueprint(results, url_prefix='/results')

cors_headers = ['Content-Type', 'Authorization']

@app.route('/')
@crossdomain(origin='*', headers=cors_headers)
def home():
    return render_template("/index.html")


def url_for_other_page(page):
    args = request.view_args.copy()
    args['page'] = page
    return url_for(request.endpoint, **args)

app.jinja_env.globals['url_for_other_page'] = url_for_other_page

if(__name__ == "__main__"):
    app.run(debug=app.config['DEBUG'], host=app.config['HOST'], port=app.config['PORT'])

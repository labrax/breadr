"""Front-end/back-end connector"""

import math
from datetime import datetime
import string
import random
import base64
import os
import json
import webbrowser
import tornado
import tornado.ioloop
import tornado.web
import tornado.template

from crumb.web.html_templates import function_list_as_html, NAV_TYPES
from crumb.web.sessions import SessionStore

loader = tornado.template.Loader('.')

BASE_PATH = os.path.dirname(os.path.abspath(__file__))

STATIC_PATH = os.path.join(BASE_PATH, 'dist/')
FAVICON_PATH = os.path.join(BASE_PATH, 'favicon.ico')
INDEX_FILE = os.path.join(BASE_PATH, 'html/index.html')
SLICE_FILE = os.path.join(BASE_PATH, 'html/slice.html')
TREE_FILE = os.path.join(BASE_PATH, 'html/tree.html')

SETTINGS = {
    "cookie_secret": base64.b64encode(os.urandom(50)).decode('ascii'),
    "login_url": "/login",
    'debug': False
}

if 'BREADR_PWD' in os.environ:
    print('Using environment password BREADR_PWD')
    BREADR_PASSWORD = os.environ['BREADR_PWD']
else:
    _ops = string.ascii_letters + string.digits
    BREADR_PASSWORD = ''.join([random.choice(_ops) for _ in range(16)])


class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        pwd = self.get_secure_cookie('password')
        if not pwd:
            return None
        return tornado.escape.json_decode(pwd)


class MainHandler(BaseHandler):
    """Render index file"""
    @tornado.web.authenticated
    def get(self):
        self.render(INDEX_FILE)


class TreeHandler(BaseHandler):
    """Display folders and files"""
    @tornado.web.authenticated
    def get(self, path):
        if path == '':
            path = '.'

        def isbreadr(file: str):
            return file.split('.')[-1] == 'json'

        def get_namelink(file: str):
            true_file = os.path.join(path, file)
            if isbreadr(true_file):  # we can open
                link = f'/slice/{true_file}'
                return f"""<a href="{link}">{file}</a>"""
            elif os.path.isfile(true_file):  # we do not open
                return file
            # folder
            link = f'/tree/{true_file}'
            return f"""<a href="{link}">{file}</a>"""

        def get_type(file: str):
            if isbreadr(file):
                return NAV_TYPES['breadr']
            elif os.path.isfile(file):
                return NAV_TYPES['file']
            return NAV_TYPES['folder']

        def get_modified(file: str):
            return datetime.fromtimestamp(os.path.getmtime(os.path.join(path, file))).strftime("%Y/%m/%d %H:%M")

        def get_size(file: str):
            if not os.path.isfile(os.path.join(path, file)):
                return ''

            def convert_size(size_bytes):  # https://stackoverflow.com/questions/5194057/better-way-to-convert-file-sizes-in-python
                if size_bytes == 0:
                    return "0 B"
                size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
                i = int(math.floor(math.log(size_bytes, 1024)))
                nsize = round(size_bytes / math.pow(1024, i), 2)
                return f"{nsize} {size_name[i]}"
            return convert_size(os.path.getsize(os.path.join(path, file)))

        def is_hidden(file: str):
            # if f[0] == '_':  # ignore '_*' files
            #     return True
            if file[0] == '.' and file[1] != '.':  # ignore '.*' files
                return True
            if file == '..' and path == '.':  # ignore ".." if on base folder
                return True
            return False

        files = []
        folders = []
        for i in os.listdir(path):
            if os.path.isfile(os.path.join(path, i)):
                files.append(i)
            else:
                folders.append(i)
        files.sort()
        folders.sort()

        _raw_files = ['..'] + folders + files
        _reported_files = [f for f in _raw_files if not is_hidden(f)]
        filefolders = {f: {'type': get_type(os.path.join(path, f)),
                           'name': get_namelink(f),
                           'size': get_size(f),
                           'modified': get_modified(f)} for f in _reported_files}
        r = loader.load(TREE_FILE).generate(filefolders=filefolders)
        self.write(r)


class LoginHandler(BaseHandler):
    def get(self):
        password = self.get_argument("password", "")
        auth = self.check_permission(password)
        if auth:
            self.set_current_user(password)
            self.redirect(self.get_argument("next", "/"))
        else:
            params = {
                "errormessage": self.get_argument("error", ''),
                "nextpage": self.get_argument("next", "/")
            }
            self.render('login.html', **params)

    def check_permission(self, password):
        """Check if password is valid"""
        if password == BREADR_PASSWORD:
            return True
        return False

    def post(self):
        password = self.get_argument("password", "")
        auth = self.check_permission(password)
        if auth:
            self.set_current_user(password)
            self.redirect(self.get_argument("next", "/"))
        else:
            self.redirect("/login" + "?error=" + tornado.escape.url_escape("Invalid password!"))

    def set_current_user(self, password):
        if password:
            self.set_secure_cookie("password", tornado.escape.json_encode(password))
        else:
            self.clear_cookie("password")


class SliceHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, file):
        r = loader.load(SLICE_FILE).generate(file=file)
        self.write(r)


class addNode(BaseHandler):
    @tornado.web.authenticated
    def post(self):
        data = tornado.escape.json_decode(self.request.body)
        print(data)
        ret = SessionStore.get_file(data['payload']['file']).addNode(data['payload']['name'], data['payload']['ele_pos_x'], data['payload']['ele_pos_y'])
        ret['operation'] = 'addNode'
        print(data, '===>', ret)
        r = json.dumps(ret)
        self.write(r)


class removeNodeId(BaseHandler):
    @tornado.web.authenticated
    def post(self):
        data = tornado.escape.json_decode(self.request.body)
        ret = {'id': data['payload']['id']}
        SessionStore.get_file(data['payload']['file']).removeNode(**ret)
        ret['operation'] = 'removeNodeId'
        print(data, '===>', ret)
        r = json.dumps(ret)
        self.write(r)


class addConnection(BaseHandler):
    @tornado.web.authenticated
    def post(self):
        data = tornado.escape.json_decode(self.request.body)
        try:
            # make changes
            ret = {'id_output': data['payload']['id_output'],
                   'id_input': data['payload']['id_input'],
                   'output_class': data['payload']['output_class'],
                   'input_class': data['payload']['input_class']}
            SessionStore.get_file(data['payload']['file']).addConnection(**ret)
            ret['operation'] = 'addConnection'
            print(data, '===>', ret)
            r = json.dumps(ret)
            self.write(r)
        except Exception as e:
            self.set_status(400)
            self.write({'error': e})


class removeConnection(BaseHandler):
    """Remove connection from input/output/internal node"""
    @tornado.web.authenticated
    def post(self):
        data = tornado.escape.json_decode(self.request.body)
        ret = {'class_list': data['payload']['class_list']}
        SessionStore.get_file(data['payload']['file']).removeConnection(**ret)
        ret['operation'] = 'removeConnection'
        print(data, '===>', ret)
        r = json.dumps(ret)
        self.write(r)


class nodeMoved(BaseHandler):
    """Save new node position"""
    @tornado.web.authenticated
    def post(self):
        data = tornado.escape.json_decode(self.request.body)
        SessionStore.get_file(data['payload']['file']).move_node(id=data['payload']['id'], x=data['payload']['pos_x'], y=data['payload']['pos_y'])
        ret = {'operation': 'nodeMoved'}
        print(data, '===>', ret)
        r = json.dumps(ret)
        self.write(r)


class zoom(BaseHandler):
    """Set zoom level"""
    @tornado.web.authenticated
    def post(self):
        data = tornado.escape.json_decode(self.request.body)
        SessionStore.get_file(data['payload']['file']).zoom(data['payload']['zoom'])
        ret = {'operation': 'zoom'}
        print(data, '===>', ret)
        r = json.dumps(ret)
        self.write(r)


class translate(BaseHandler):
    """Translate position"""
    @tornado.web.authenticated
    def post(self):
        data = tornado.escape.json_decode(self.request.body)
        SessionStore.get_file(data['payload']['file']).translate(data['payload']['x'], data['payload']['y'])
        ret = {'operation': 'translate'}
        print(data, '===>', ret)
        r = json.dumps(ret)
        self.write(r)


class refresh(BaseHandler):
    """Refresh and get the list of Crumbs/Slices available"""
    @tornado.web.authenticated
    def post(self):
        data = tornado.escape.json_decode(self.request.body)
        ret = {'html': function_list_as_html(SessionStore.get_file(data['payload']['file']).get_function_list())}
        ret['operation'] = 'refresh'
        print(data, '===>', ret)
        r = json.dumps(ret)
        self.write(r)


class run(BaseHandler):
    """Run the slice"""
    @tornado.web.authenticated
    def post(self):
        data = tornado.escape.json_decode(self.request.body)
        all_output = SessionStore.get_file(data['payload']['file']).run()
        ret = {'output': all_output}
        ret['operation'] = 'run'
        print(data, '===>', ret)
        r = json.dumps(ret)
        self.write(r)


class setParameter(BaseHandler):
    """Set the type of a input/output parameter"""
    @tornado.web.authenticated
    def post(self):
        data = tornado.escape.json_decode(self.request.body)
        ret = {'node': data['payload']['node'], 'name': data['payload']['name'], 'type': data['payload']['type']}
        SessionStore.get_file(data['payload']['file']).setParameter(**ret)
        ret['operation'] = 'setParameter'
        print(data, '===>', ret)
        r = json.dumps(ret)
        self.write(r)


class save(BaseHandler):
    """Handle save calls"""
    @tornado.web.authenticated
    def post(self):
        data = tornado.escape.json_decode(self.request.body)
        SessionStore.get_file(data['payload']['file']).save()
        ret = {'status': 'ok'}
        ret['operation'] = 'save'
        print(data, '===>', ret)
        r = json.dumps(ret)
        self.write(r)


def web_app():
    """Run Breadr web server"""
    app = tornado.web.Application([
        (r"/", MainHandler),
        (r"/login", LoginHandler),
        (r"/tree/(.*)", TreeHandler),
        (r"/slice/(.*)", SliceHandler),
        (r"/api/v1/addNode", addNode),
        (r"/api/v1/removeNodeId", removeNodeId),
        (r"/api/v1/addConnection", addConnection),
        (r"/api/v1/removeConnection", removeConnection),
        (r"/api/v1/nodeMoved", nodeMoved),
        (r"/api/v1/zoom", zoom),
        (r"/api/v1/translate", translate),
        (r"/api/v1/refresh", refresh),
        (r"/api/v1/setParameter", setParameter),
        (r"/api/v1/save", save),

        (r'/(favicon.ico)', tornado.web.StaticFileHandler, {"path": FAVICON_PATH}),
        (r'/dist/(.*)', tornado.web.StaticFileHandler, {'path': STATIC_PATH})
    ], **SETTINGS)
    app.listen(8080, '127.0.0.1')
    url = f'http://127.0.0.1:8080/login?password={BREADR_PASSWORD}'
    print(f'Opening browser for {url}')
    webbrowser.open_new_tab(url)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    web_app()

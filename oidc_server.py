import os
import typing as t

from flask import Flask, request
from flask_oidc import OpenIDConnect, MemoryCredentials


class OidcServer(Flask):
    class MyOpenIDConnect(OpenIDConnect):

        def __init__(self, oauth_server, client_id, client_secret, app=None, credentials_store=None, http=None, time=None, urandom=None, self_host="http://localhost:5000"):
            self.oauth_server = oauth_server
            self.client_id = client_id
            self.client_secret = client_secret
            self.self_host = self_host
            app.config["OIDC_CLIENT_SECRETS"] = self.load_secrets(app)
            super().__init__(app, credentials_store or MemoryCredentials(), http, time, urandom)

        def load_secrets(self, app):
            return {"web": {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "auth_uri": ("%s/protocol/openid-connect/auth" % self.oauth_server),
                "token_uri": ("%s/protocol/openid-connect/token" % self.oauth_server),
                "userinfo_uri": ("%s/protocol/openid-connect/userinfo" % self.oauth_server),
                "redirect_uris": [("%s/oidc_callback" % self.self_host)],
                "issuer": ("%s" % self.oauth_server)
            }}

    def __init__(self, import_name: str, oauth_server, client_id, client_secret, static_url_path: t.Optional[str] = None,
                 static_folder: t.Optional[str] = "static", static_host: t.Optional[str] = None,
                 host_matching: bool = False, subdomain_matching: bool = False,
                 template_folder: t.Optional[str] = "templates", instance_path: t.Optional[str] = None,
                 instance_relative_config: bool = False, root_path: t.Optional[str] = None):
        self.secured_endpoints = []
        super().__init__(import_name, static_url_path, static_folder, static_host, host_matching, subdomain_matching,
                         template_folder, instance_path, instance_relative_config, root_path)

        self.config['SECRET_KEY'] = "My default App Secret"

        self.oidc = OidcServer.MyOpenIDConnect(app=self, oauth_server=oauth_server, client_id=client_id, client_secret=client_secret)

        @self.before_request
        def before_request():
            for endpoint in self.secured_endpoints:
                if request.path.startswith(endpoint):
                    return self.oidc.authenticate_or_redirect()

    def add_url_rule(self, rule: str, endpoint: t.Optional[str] = None, view_func: t.Optional[t.Callable] = None,
                     provide_automatic_options: t.Optional[bool] = None, **options: t.Any) -> None:
        if rule != "/oidc_callback":
            self.add_secured(endpoint)
        super().add_url_rule(rule, endpoint, view_func, provide_automatic_options, **options)

    def add_secured(self, endpoint):
        if not endpoint.startswith("/"):
            endpoint = "/" + endpoint
        print(f"Securing {endpoint}")
        self.secured_endpoints.append(endpoint)


from owrx.controllers import Controller


class RobotsController(Controller):
    def indexAction(self):
        # search engines should not be crawling internal / API routes
        self.send_response(
            """User-agent: *
Disallow: /login
Disallow: /logout
Disallow: /pwchange
Disallow: /settings
Disallow: /imageupload
""",
            content_type="text/plain",
        )

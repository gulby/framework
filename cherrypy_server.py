# Import your application as:
# from wsgi import application
# Example:

from server.wsgi import application

# Import CherryPy
import cherrypy
import sys


if __name__ == "__main__":
    # Mount the application
    cherrypy.tree.graft(application, "/")

    # Unsubscribe the default server
    cherrypy.server.unsubscribe()

    # Instantiate a new server object
    server = cherrypy._cpserver.Server()

    # Configure the server object
    server.socket_host = "0.0.0.0"
    server.socket_port = int(sys.argv[1])
    server.thread_pool = 10

    # Subscribe this server
    server.subscribe()

    # Start the server engine (Option 1 *and* 2)

    cherrypy.engine.start()
    cherrypy.engine.block()

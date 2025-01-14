#!/usr/bin/python3
# GPL V2, author phe

__module_name__ = "dummy_robot"
__module_version__ = "1.0"
__module_description__ = "dummy robot"

import sys
from common import tool_connect
from common import common_html

import os
import _thread
import time
from common import job_queue

E_ERROR = 1
E_OK = 0


def ret_val(error, text):
    if error:
        print(f"Error: {error}, {text}", file=sys.stderr)
    return {'error': error, 'text': text}


def do_exec(title, cmd):
    if cmd == 'timeout':
        time.sleep(60)
        return ret_val(E_ERROR, "timeout: 60 sec: " + title)

    return ret_val(E_OK, "exec ok: " + title)


# cmd title t tools conn
def html_for_queue(queue):
    html = ''
    for i in queue:
        mtitle = i[1]

        html += date_s(i[1]) + ' ' + mtitle + "<br/>"
    return html


def do_status(queue):
    queue = queue.copy_items(True)

    html = common_html.get_head('Dummy robot')
    html += "<body><div>The robot is running.<br/><hr/>"
    html += "<br/>%d jobs in dummy robot queue.<br/>" % len(queue)
    html += html_for_queue(queue)
    html += '</div></body></html>'
    return html


def bot_listening(queue):
    print(date_s(time.time()) + " START")

    tools = tool_connect.ToolConnect('dummy_robot', 45139)

    try:
        while True:
            request, conn = tools.wait_request()

            try:
                print(request)

                cmd = request['cmd']
                title = request.get('title', '')
            except:
                ret = ret_val(E_ERROR, "invalid request")
                tools.send_reply(conn, ret)
                conn.close()
                continue

            t = time.time()

            print(f'{date_s(t)} REQUEST {cmd} {title}')

            if cmd in ["exec", "timeout"]:
                queue.put(cmd, title, t, tools, conn)
            elif cmd == 'status':
                html = do_status(queue)
                tools.send_text_reply(conn, html)
                conn.close()
            elif cmd == 'ping':
                tools.send_reply(conn, ret_val(E_OK, 'pong'))
                conn.close()
            else:
                tools.send_reply(conn, ret_val(E_ERROR, "unknown command: " + cmd))
                conn.close()

    finally:
        tools.close()
        print("STOP", file=sys.stderr)


def date_s(at):
    t = time.gmtime(at)
    return time.strftime("%d/%m/%Y:%H:%M:%S", t)


def job_thread(queue, func):
    while True:
        cmd, title, t, tools, conn = queue.get()

        time1 = time.time()

        out = func(title, cmd)

        if tools and conn:
            tools.send_reply(conn, out)
            conn.close()

        time2 = time.time()
        print(f'{date_s(time2)} {title} ({time2 - time1:.2f})')

        queue.remove()


if __name__ == "__main__":
    try:
        queue = job_queue.JobQueue()
        _thread.start_new_thread(job_thread, (queue, do_exec))
        bot_listening(queue)
    except KeyboardInterrupt:
        os._exit(1)
#    finally:
#        pywikibot.stopme()

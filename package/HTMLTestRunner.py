#coding=utf-8
"""
A TestRunner for use with the Python unit testing framework. It
generates a HTML report to show the result at a glance.

Customized version (English UI) -- originally modified by YinJia (CN).
"""

__author__ = "Qun Li"
__version__ = "0.8.2"

import datetime
import io
import sys
import time
import unittest
from xml.sax import saxutils


class OutputRedirector(object):
    """ Wrapper to redirect stdout or stderr """
    def __init__(self, fp):
        self.fp = fp

    def write(self, s):
        self.fp.write(s)

    def writelines(self, lines):
        self.fp.writelines(lines)

    def flush(self):
        self.fp.flush()


stdout_redirector = OutputRedirector(sys.stdout)
stderr_redirector = OutputRedirector(sys.stderr)


class Template_mixin(object):
    """
    Define a HTML template for report customization and generation.
    """

    # ✅ English status labels for UI
    STATUS = {
        0: 'PASS',
        1: 'FAIL',
        2: 'ERROR',
    }

    DEFAULT_TITLE = 'Unit Test Report'
    DEFAULT_DESCRIPTION = ''
    DEFAULT_TESTER = 'QA'


    HTML_TMPL = r"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>%(title)s</title>
    <meta name="generator" content="%(generator)s"/>
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>
    %(stylesheet)s
</head>
<body>
<script language="javascript" type="text/javascript"><!--
output_list = Array();

/* level - 0:Summary; 1:Failed; 2:Passed; 3:All */
function showCase(level) {
    trs = document.getElementsByTagName("tr");
    for (var i = 0; i < trs.length; i++) {
        tr = trs[i];
        id = tr.id;
        if (id.substr(0,2) == 'ft') {
            if (level == 2 || level == 0) {
                tr.className = 'hiddenRow';
            }
            else {
                tr.className = '';
            }
        }
        if (id.substr(0,2) == 'pt') {
            if (level < 2) {
                tr.className = 'hiddenRow';
            }
            else {
                tr.className = '';
            }
        }
    }
}

function showClassDetail(cid, count) {
    var id_list = Array(count);
    var toHide = 1;
    for (var i = 0; i < count; i++) {
        tid0 = 't' + cid.substr(1) + '.' + (i+1);
        tid = 'f' + tid0;
        tr = document.getElementById(tid);
        if (!tr) {
            tid = 'p' + tid0;
            tr = document.getElementById(tid);
        }
        id_list[i] = tid;
        if (tr.className) {
            toHide = 0;
        }
    }
    for (var i = 0; i < count; i++) {
        tid = id_list[i];
        if (toHide) {
            document.getElementById('div_'+tid).style.display = 'none'
            document.getElementById(tid).className = 'hiddenRow';
        }
        else {
            document.getElementById(tid).className = '';
        }
    }
}

function showTestDetail(div_id){
    var details_div = document.getElementById(div_id)
    var displayState = details_div.style.display
    if (displayState != 'block' ) {
        displayState = 'block'
        details_div.style.display = 'block'
    }
    else {
        details_div.style.display = 'none'
    }
}

function html_escape(s) {
    s = s.replace(/&/g,'&amp;');
    s = s.replace(/</g,'&lt;');
    s = s.replace(/>/g,'&gt;');
    return s;
}

/* Pie chart */
function drawCircle(pass, fail, error){
    var color = ["#6c6","#c60","#c00"];
    var data = [pass,fail,error];
    var text_arr = ["pass", "fail", "error"];

    var canvas = document.getElementById("circle");
    var ctx = canvas.getContext("2d");
    var startPoint=0;
    var width = 20, height = 10;
    var posX = 112 * 2 + 20, posY = 30;
    var textX = posX + width + 5, textY = posY + 10;
    for(var i=0;i<data.length;i++){
        ctx.fillStyle = color[i];
        ctx.beginPath();
        ctx.moveTo(112,84);
        ctx.arc(112,84,84,startPoint,startPoint+Math.PI*2*(data[i]/(data[0]+data[1]+data[2])),false);
        ctx.fill();
        startPoint += Math.PI*2*(data[i]/(data[0]+data[1]+data[2]));
        ctx.fillStyle = color[i];
        ctx.fillRect(posX, posY + 20 * i, width, height);
        ctx.moveTo(posX, posY + 20 * i);
        ctx.font = 'bold 14px';
        ctx.fillStyle = color[i];
        var percent = text_arr[i] + ":"+data[i];
        ctx.fillText(percent, textX, textY + 20 * i);

    }
}

function show_shots(obj) {
    obj.nextElementSibling.style.display="block";
}

function close_shots(obj) {
    obj.parentElement.style.display="none";
}

--></script>
<div class="piechart">
    <div>
        <canvas id="circle" width="350" height="168" </canvas>
    </div>
</div>
%(heading)s
%(report)s
%(ending)s

</body>
</html>
"""


    STYLESHEET_TMPL = """
<style type="text/css" media="screen">
body        { font-family: verdana, arial, helvetica, sans-serif; font-size: 80%; }
table       { font-size: 100%; }
pre         { }

/* -- heading ---------------------------------------------------------------------- */
h1 {
    font-size: 16pt;
    color: gray;
}
.heading {
    margin-top: 0ex;
    margin-bottom: 1ex;
}
.heading .attribute {
    margin-top: 1ex;
    margin-bottom: 0;
}
.heading .description {
    margin-top: 4ex;
    margin-bottom: 6ex;
}

/* -- css div popup ------------------------------------------------------------------------ */
a.popup_link {
}
a.popup_link:hover {
    color: red;
}
.img{
    width: 100%;
    height: 100%;
    border-collapse: collapse;
    border: 2px solid #777;
}
.screenshots {
    z-index: 100;
    position:absolute;
    left: 23%;
    top: 20%;
    display: none;
}
.close_shots {
    position:absolute;
    top:0; left:98%;
    z-index:99;
    width:20px;
}
.popup_window {
    display: none;
    position: relative;
    left: 0px;
    top: 0px;
    padding: 10px;
    background-color: #E6E6D6;
    font-family: "Lucida Console", "Courier New", Courier, monospace;
    text-align: left;
    font-size: 8pt;
    width: 800px;
}

}
/* -- report ------------------------------------------------------------------------ */
#show_detail_line {
    margin-top: 3ex;
    margin-bottom: 1ex;
}
#result_table {
    width: 80%;
    border-collapse: collapse;
    border: 1px solid #777;
}
#header_row {
    font-weight: bold;
    color: white;
    background-color: #777;
}
#result_table td {
    border: 1px solid #777;
    padding: 2px;
}
#total_row  { font-weight: bold; }
.passClass  { background-color: #6c6; }
.failClass  { background-color: #c60; }
.errorClass { background-color: #c00; }
.passCase   { color: #6c6; font-weight: bold;}
.failCase   { color: #c60; font-weight: bold; }
.errorCase  { color: #c00; font-weight: bold; }
.hiddenRow  { display: none; }
.testcase   { margin-left: 2em; }

/* -- ending ---------------------------------------------------------------------- */
#ending {
}
.piechart{
    position:absolute;
    top:20px;
    left:60%;
    min-width: 220px;
    width: 220px;
    display: inline;
}
</style>
"""


    HEADING_TMPL = """<div class='heading'>
<h1>%(title)s</h1>
%(parameters)s
<p class='description'>%(description)s</p>
</div>
"""

    HEADING_ATTRIBUTE_TMPL = """<p class='attribute'><strong>%(name)s:</strong> %(value)s</p>
"""


    REPORT_TMPL = """
<p id='show_detail_line'>View:
<a href='javascript:showCase(0)'>Summary</a>
<a href='javascript:showCase(1)'>Failed[%(fail)s]</a>
<a href='javascript:showCase(2)'>Passed[%(Pass)s]</a>
<a href='javascript:showCase(3)'>All[%(count)s]</a>
</p>
<table id='result_table'>
<colgroup>
<col align='left' />
<col align='right' />
<col align='right' />
<col align='right' />
<col align='right' />
<col align='right' />
<col align='right' />
</colgroup>
<tr id='header_row'>
    <td>Test Suite / Test Case</td>
    <td>Total</td>
    <td>Passed</td>
    <td>Failed</td>
    <td>Error</td>
    <td>Details</td>
    <td>Screenshot</td>
</tr>
%(test_list)s
<tr id='total_row'>
    <td>Total</td>
    <td>%(count)s</td>
    <td>%(Pass)s</td>
    <td>%(fail)s</td>
    <td>%(error)s</td>
    <td>Pass Rate: %(passrate)s</td>
    <td>&nbsp;</td>
</tr>
</table>
<script>
    drawCircle(%(Pass)s, %(fail)s, %(error)s)
</script>
"""

    REPORT_CLASS_TMPL = r"""
<tr class='%(style)s'>
    <td>%(desc)s</td>
    <td>%(count)s</td>
    <td>%(Pass)s</td>
    <td>%(fail)s</td>
    <td>%(error)s</td>
    <td><a href="javascript:showClassDetail('%(cid)s',%(count)s)">View</a></td>
    <td>&nbsp;</td>
</tr>
"""

    REPORT_TEST_WITH_OUTPUT_TMPL = r"""
    <tr id='%(tid)s' class='%(Class)s'>
        <td class='%(style)s'><div class='testcase'>%(desc)s</div></td>
        <td colspan='5' align='center'>

        <a class="popup_link" onfocus='this.blur();' href="javascript:showTestDetail('div_%(tid)s')" >
            %(status)s</a>

        <div id='div_%(tid)s' class="popup_window">
            <div style='text-align: right; color:red;cursor:pointer'>
            <a onfocus='this.blur();' onclick="document.getElementById('div_%(tid)s').style.display = 'none' " >
               [x]</a>
            </div>
            <pre>
            %(script)s
            </pre>
        </div>
    </td>
    <td>%(img)s</td>
</tr>
"""

    REPORT_TEST_NO_OUTPUT_TMPL = r"""
<tr id='%(tid)s' class='%(Class)s'>
    <td class='%(style)s'><div class='testcase'>%(desc)s</div></td>
    <td colspan='5' align='center'>%(status)s</td>
    <td>%(img)s</td>
</tr>
"""

    REPORT_TEST_OUTPUT_TMPL = r"""
%(id)s: %(output)s
"""

    ENDING_TMPL = """<div id='ending'>&nbsp;</div>"""


TestResult = unittest.TestResult


class _TestResult(TestResult):
    def __init__(self, verbosity=2):
        TestResult.__init__(self)
        self.stdout0 = None
        self.stderr0 = None
        self.success_count = 0
        self.failure_count = 0
        self.error_count = 0
        self.verbosity = verbosity
        self.result = []
        self.passrate = float(0)
        self.status = 0

    def startTest(self, test):
        TestResult.startTest(self, test)
        test.img = ""
        self.outputBuffer = io.StringIO()
        stdout_redirector.fp = self.outputBuffer
        stderr_redirector.fp = self.outputBuffer
        self.stdout0 = sys.stdout
        self.stderr0 = sys.stderr
        sys.stdout = stdout_redirector
        sys.stderr = stderr_redirector

    def complete_output(self):
        if self.stdout0:
            sys.stdout = self.stdout0
            sys.stderr = self.stderr0
            self.stdout0 = None
            self.stderr0 = None
        return self.outputBuffer.getvalue()

    def stopTest(self, test):
        self.complete_output()

    def addSuccess(self, test):
        self.success_count += 1
        self.status = 0
        TestResult.addSuccess(self, test)
        output = self.complete_output()
        self.result.append((0, test, output, ''))
        if self.verbosity > 1:
            sys.stderr.write('ok ')
            sys.stderr.write(str(test))
            sys.stderr.write('\n')
        else:
            sys.stderr.write('.')

    def addError(self, test, err):
        self.error_count += 1
        self.status = 1
        TestResult.addError(self, test, err)
        _, _exc_str = self.errors[-1]
        output = self.complete_output()
        self.result.append((2, test, output, _exc_str))
        try:
            driver = getattr(test, "driver")
            test.img = driver.get_screenshot_as_base64()
        except AttributeError:
            test.img = ""
        if self.verbosity > 1:
            sys.stderr.write('E  ')
            sys.stderr.write(str(test))
            sys.stderr.write('\n')
        else:
            sys.stderr.write('E')

    def addFailure(self, test, err):
        self.failure_count += 1
        self.status = 1
        TestResult.addFailure(self, test, err)
        _, _exc_str = self.failures[-1]
        output = self.complete_output()
        self.result.append((1, test, output, _exc_str))
        try:
            driver = getattr(test, "driver")
            test.img = driver.get_screenshot_as_base64()
        except AttributeError:
            test.img = ""
        if self.verbosity > 1:
            sys.stderr.write('F  ')
            sys.stderr.write(str(test))
            sys.stderr.write('\n')
        else:
            sys.stderr.write('F')


class HTMLTestRunner(Template_mixin):
    def __init__(self, stream=sys.stdout, verbosity=2, title=None, description=None, tester=None):
        self.stream = stream
        self.verbosity = verbosity

        self.title = self.DEFAULT_TITLE if title is None else title
        self.description = self.DEFAULT_DESCRIPTION if description is None else description
        self.tester = self.DEFAULT_TESTER if tester is None else tester

        self.startTime = datetime.datetime.now()

    def run(self, test):
        result = _TestResult(self.verbosity)
        test(result)
        self.stopTime = datetime.datetime.now()
        self.generateReport(test, result)
        print(sys.stderr, '\nTime Elapsed: %s' % (self.stopTime - self.startTime))
        return result

    def sortResult(self, result_list):
        rmap = {}
        classes = []
        for n, t, o, e in result_list:
            cls = t.__class__
            if not cls in rmap:
                rmap[cls] = []
                classes.append(cls)
            rmap[cls].append((n, t, o, e))
        r = [(cls, rmap[cls]) for cls in classes]
        return r

    def getReportAttributes(self, result):
        startTime = str(self.startTime)[:19]
        duration = str(self.stopTime - self.startTime)

        total = result.success_count + result.failure_count + result.error_count
        status_parts = [f"Total {total}"]
        if result.success_count:
            status_parts.append(f"Passed {result.success_count}")
        if result.failure_count:
            status_parts.append(f"Failed {result.failure_count}")
        if result.error_count:
            status_parts.append(f"Error {result.error_count}")

        if total > 0:
            self.passrate = str("%.2f%%" % (float(result.success_count) / float(total) * 100))
        else:
            self.passrate = "0.00%"

        status = " ".join(status_parts) + f" | Pass Rate = {self.passrate}"

        return [
            ('Tester', self.tester),
            ('Start Time', startTime),
            ('Duration', duration),
            ('Summary', status),
        ]

    def generateReport(self, test, result):
        report_attrs = self.getReportAttributes(result)
        generator = 'HTMLTestRunner %s' % __version__
        stylesheet = self._generate_stylesheet()
        heading = self._generate_heading(report_attrs)
        report = self._generate_report(result)
        ending = self._generate_ending()
        output = self.HTML_TMPL % dict(
            title=saxutils.escape(self.title),
            generator=generator,
            stylesheet=stylesheet,
            heading=heading,
            report=report,
            ending=ending,
        )
        self.stream.write(output.encode('utf8'))

    def _generate_stylesheet(self):
        return self.STYLESHEET_TMPL

    def _generate_heading(self, report_attrs):
        a_lines = []
        for name, value in report_attrs:
            line = self.HEADING_ATTRIBUTE_TMPL % dict(
                name=saxutils.escape(name),
                value=saxutils.escape(value),
            )
            a_lines.append(line)
        heading = self.HEADING_TMPL % dict(
            title=saxutils.escape(self.title),
            parameters=''.join(a_lines),
            description=saxutils.escape(self.description),
            tester=saxutils.escape(self.tester),
        )
        return heading

    def _generate_report(self, result):
        rows = []
        sortedResult = self.sortResult(result.result)
        for cid, (cls, cls_results) in enumerate(sortedResult):
            np = nf = ne = 0
            for n, t, o, e in cls_results:
                if n == 0:
                    np += 1
                elif n == 1:
                    nf += 1
                else:
                    ne += 1

            if cls.__module__ == "__main__":
                name = cls.__name__
            else:
                name = "%s.%s" % (cls.__module__, cls.__name__)
            doc = cls.__doc__ and cls.__doc__.split("\n")[0] or ""
            desc = doc and '%s: %s' % (name, doc) or name

            row = self.REPORT_CLASS_TMPL % dict(
                style=ne > 0 and 'errorClass' or nf > 0 and 'failClass' or 'passClass',
                desc=desc,
                count=np + nf + ne,
                Pass=np,
                fail=nf,
                error=ne,
                cid='c%s' % (cid + 1),
            )
            rows.append(row)

            for tid, (n, t, o, e) in enumerate(cls_results):
                self._generate_report_test(rows, cid, tid, n, t, o, e)

        report = self.REPORT_TMPL % dict(
            test_list=''.join(rows),
            count=str(result.success_count + result.failure_count + result.error_count),
            Pass=str(result.success_count),
            fail=str(result.failure_count),
            error=str(result.error_count),
            passrate=self.passrate,
        )
        return report

    def _generate_report_test(self, rows, cid, tid, n, t, o, e):
        has_output = bool(o or e)
        tid = (n == 0 and 'p' or 'f') + 't%s.%s' % (cid + 1, tid + 1)
        name = t.id().split('.')[-1]
        doc = t.shortDescription() or ""
        desc = doc and ('%s: %s' % (name, doc)) or name
        tmpl = has_output and self.REPORT_TEST_WITH_OUTPUT_TMPL or self.REPORT_TEST_NO_OUTPUT_TMPL

        if isinstance(o, str):
            uo = o
        else:
            uo = o
        if isinstance(e, str):
            ue = e
        else:
            ue = e

        script = self.REPORT_TEST_OUTPUT_TMPL % dict(
            id=tid,
            output=saxutils.escape(uo + ue),
        )

        if t.img:
            img = """
                    <a href="#" onclick="show_shots(this)">View Screenshot</a>
                    <div class="screenshots">
                    <a  class="close_shots" onclick="close_shots(this)">X</a>
                    <img src="data:image/jpg;base64,%s" class="img"/>
                    </div>""" % t.img
        else:
            img = """"""

        row = tmpl % dict(
            tid=tid,
            Class=(n == 0 and 'hiddenRow' or 'none'),
            style=n == 2 and 'errorCase' or (n == 1 and 'failCase' or 'passCase'),
            desc=desc,
            script=script,
            status=self.STATUS[n],
            img=img,
        )
        rows.append(row)
        if not has_output:
            return

    def _generate_ending(self):
        return self.ENDING_TMPL


class TestProgram(unittest.TestProgram):
    def runTests(self):
        if self.testRunner is None:
            self.testRunner = HTMLTestRunner(verbosity=self.verbosity)
        unittest.TestProgram.runTests(self)


main = TestProgram


if __name__ == "__main__":
    main(module=None)

DemoAPI

This document summarizes the design and implementation of an
<u>API testing framework</u>.

The environment is based on
<u>Python 3</u> + <u>unittest</u> + <u>DDT (data-driven testing)</u>.

Test cases and test data are managed using
<u>Excel</u>, and <u>HTMLTestRunner</u> is used to generate
<u>test reports</u>.

Currently, there are many <u>open-source API testing tools</u> such as
<u>Postman</u> and <u>JMeter</u>.

So why do we still need to build a
<u>custom API testing framework</u>?

Because existing API testing tools have several limitations:

• <u>Test data is not controllable</u>.
For example, when <u>API response data changes dynamically</u>,
it is difficult to perform <u>stable assertions</u>.
It becomes unclear whether failures are caused by
<u>code defects</u> or by <u>test data changes</u>.
Therefore, <u>test data initialization</u> is required.

• <u>Limited extensibility</u>.
Open-source API testing tools are difficult to <u>extend</u>.
For example, customizing <u>test report formats</u> or integrating API tests into
<u>CI pipelines</u> for <u>scheduled execution</u>
is often inconvenient or unsupported.

API Testing Framework Workflow
<img src="share/screenshots/Summary.png" width="800">

The overall testing workflow is as follows:

• Call the <u>target system APIs</u>,
using <u>data-driven testing</u> to read test cases
<u>line by line from Excel</u>.

• Send <u>API requests</u> and compare <u>API responses</u>
with <u>expected values</u> defined in Excel.

• Use the <u>unittest framework</u> to assert API responses
and generate <u>HTML test reports</u>.

Project Directory Structure

The project directory structure is organized as follows:

• <u>config/</u>
Path and <u>environment configuration files</u>

• <u>database/</u>
<u>Test case templates</u> and <u>configuration files</u>

• <u>lib/</u>
<u>Core framework modules</u>, including
<u>Excel read/write</u> and <u>request handling</u>

• <u>package/</u>
<u>Third-party libraries</u>, such as <u>HTMLTestRunner</u>,
used to generate <u>HTML test reports</u>

• <u>report/</u>
Generated <u>API automation test reports</u>

• <u>testcase/</u>
<u>API automation test cases</u>

• <u>run_demo.py</u>
<u>Main entry script</u> to execute all API test cases
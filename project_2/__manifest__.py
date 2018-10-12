# -*- coding: utf-8 -*-
{
    'name': "choice organochem",

    'summary': """
        This module is built specifically for Choice organochem llp.""",

    'description': """
        This module is built keeping in mind the specific requirments of choice organochem llp.\n
        website: http://www.choiceorganochem.in
    """,

    'author': "MakBridge",
    'website': "http://www.makbridge.com",
    'category': 'Uncategorized',
    'version': '0.1',

    'depends': ['base','contacts','mail','project'],
    
    "css": [
                "static/src/lib/jquery.timerpicker/jquery.timepicker.css",
                "static/src/css/web_widget_timepicker.css",
            ],
    "js": [
                "static/src/lib/jquery.timerpicker/jquery.timepicker.js",
                "static/src/js/web_widget_timepicker.js",
            ],


    'data': [
             'data/deadline_reminder_action_data.xml',
             'views/task_management.xml',
             'views/tags.xml',
             'views/check_list.xml',
             'views/deadline_reminder_cron.xml',
             'views/web_widget_timepicker_assets.xml',
             'views/task_summary.xml',
             'views/task_assign_template.xml',
             'views/report_tree_view.xml',
             'security/security.xml',
             'views/report_excel_view.xml',
             'views/task_report_view.xml',
             'security/ir.model.access.csv',
             'views/to_do_report.xml'
	     
            ],
    
    "qweb": [
                "static/src/xml/web_widget_timepicker.xml",
            ]


}

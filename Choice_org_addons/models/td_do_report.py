from odoo import models, fields, api, _, SUPERUSER_ID

def nameBox(row, col,  row_abs=None, col_abs=None):
		cell = ''
		cell = xl_rowcol_to_cell(row, col)
		return cell

class ToDoReport(model.TransientModel):
	_name='todo.report'
	_description="To Do Report"	

	@api.multi
    def print_to_do_report(self):
        for rec in self:
            date_from=rec.date_from
            date_to=rec.date_to
            if date_from > date_to:
                 raise ValidationError(_('Please Select Proper Date.'))                
        fp = StringIO()
        workbook = xls.Workbook(fp)
        
        header_format = workbook.add_format({
                                        'bold': 1,
                                        'align': 'center',
                                        'valign': 'vcenter',
                                        'text_wrap':1,
                                        'font_name':'Verdana',
                                        'font_size':10,
                                        })
        data_format = workbook.add_format({
                                        'align': 'center',
                                        'valign': 'vcenter',
                                        'text_wrap':1,
                                        'font_name':'Verdana',
                                        'font_size':10,
                                        })
        
        no_data_format = workbook.add_format({
                                        'align': 'center',
                                        'valign': 'vcenter',
                                        'text_wrap':1,
                                        'font_name':'Verdana',
                                        'font_size':10,
                                        'font_color':'red',
                                        })
        
        merge_format = workbook.add_format({
                                        'align': 'center',
                                        'valign': 'vcenter',
                                        'text_wrap':1,
                                        'font_name':'Verdana',
                                        'font_size':10,
                                        'bold' : 1,
                                        })
        
        bold = workbook.add_format({'bold': True , 'bg_color':'#808080','font_color':'black'})
        file_name = 'To Do Reports.xlsx'
        report_name = 'To Do Report'
        worksheet = workbook.add_worksheet(report_name)

        title = "To Do Report:"
        worksheet.merge_range(0, 5, 0, 10,title,header_format)
        worksheet.write('A2:A2','Sr. No.',header_format)
        worksheet.write('C2:C2','Task Type',header_format)
        worksheet.write('B2:B2','Task Priority',header_format)
        worksheet.write('H2:H2','Deadline',header_format)
        worksheet.write('I2:I2','Allocated Time',header_format)
        worksheet.write('Q2:Q2','% of Completion',header_format)
        worksheet.write('D2:D2','Task Name',header_format)
        worksheet.write('S2:S2','Comments',header_format)

        task_search_ids = self.env['task.management'].search([('current_date','=',todays_date),
                                            ('assigned_to','=',self.employee_id.id)])
        print "\n\n_______task_search_ids_______",task_search_ids

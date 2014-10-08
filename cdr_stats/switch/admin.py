#
# http://www.cdr-stats.org
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (C) 2011-2014 Star2Billing S.L.
#
# The Initial Developer of the Original Code is
# Arezqui Belaid <info@star2billing.com>
#
from django.contrib import admin
from django.conf.urls import patterns
from django.http import HttpResponse, Http404
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.conf import settings
from django_lets_go.common_functions import mongodb_str_filter, \
    mongodb_int_filter, ceil_strdate, striplist
from switch.models import Switch
from cdr.models import CDR, CDR_SOURCE_TYPE
from cdr.forms import CDR_FileImport
from cdr.functions_def import get_hangupcause_id, get_hangupcause_id_from_name
from cdr.import_cdr_freeswitch_mongodb import apply_index, \
    create_analytic, generate_global_cdr_record
from cdr.functions_def import get_hangupcause_name
from cdr.forms import CdrSearchForm
from cdr.constants import CDR_COLUMN_NAME, Export_choice, CDR_FIELD_LIST, CDR_FIELD_LIST_NUM
from cdr.views import cdr_view_daily_report, get_pagination_vars
from cdr_alert.functions_blacklist import chk_destination
from datetime import datetime
from dateutil.relativedelta import relativedelta
import logging
import tablib
import csv
from mongodb_connection import mongodb
from django_lets_go.common_functions import getvar, unset_session_var

# Register your models here.



class SwitchAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'ipaddress', 'key_uuid')
    list_filter = ['name', 'ipaddress']
    search_fields = ('name', 'ipaddress',)

    # def get_urls(self):
    #     urls = super(SwitchAdmin, self).get_urls()
    #     my_urls = patterns('',
    #         (r'^import_cdr/$', self.admin_site.admin_view(self.import_cdr)),
    #         (r'^cdr_view/$', self.admin_site.admin_view(self.cdr_view)),
    #         (r'^export_cdr/$', self.admin_site.admin_view(self.export_cdr)),
    #     )
    #     return my_urls + urls

    # def import_cdr(self, request):
    #     """Add custom method in django admin view to import CSV file of
    #     cdr

    #     **Attributes**:

    #         * ``form`` - CDR_FileImport
    #         * ``template`` - admin/cdr/switch/import_cdr.html

    #     **Logic Description**:


    #     **Important variable**:

    #         * total_rows - Total no. of records in the CSV file
    #         * retail_record_count - No. of records which are imported from
    #           The CSV file
    #     """
    #     opts = Switch._meta
    #     app_label = opts.app_label
    #     rdr = ''  # will contain CSV data
    #     msg = ''
    #     success_import_list = []
    #     error_import_list = []
    #     type_error_import_list = []
    #     form = CDR_FileImport(request.user, request.POST or None, request.FILES or None)

    #     if form.is_valid():
    #         field_list = {}
    #         field_notin_list = []
    #         for i in CDR_FIELD_LIST:
    #             if int(request.POST[i]) != 0:
    #                 field_list[i] = int(request.POST[i])
    #             else:
    #                 field_notin_list.append((i))

    #         # perform sorting & get unique order list
    #         countMap = {}
    #         for v in field_list.itervalues():
    #             countMap[v] = countMap.get(v, 0) + 1
    #         uni = [(k, v) for k, v in field_list.iteritems() if countMap[v] == 1]
    #         uni = sorted(uni, key=lambda uni: uni[1])

    #         # if order list matched with CDR_FIELD_LIST count
    #         if len(uni) == len(CDR_FIELD_LIST) - len(field_notin_list):

    #             # To count total rows of CSV file
    #             records = csv.reader(request.FILES['csv_file'], delimiter=',', quotechar='"')
    #             total_rows = len(list(records))

    #             rdr = csv.reader(request.FILES['csv_file'], delimiter=',', quotechar='"')
    #             cdr_record_count = 0

    #             #Store cdr in list to insert by bulk
    #             cdr_bulk_record = []
    #             local_count_import = 0
    #             PAGE_SIZE = 1000

    #             # Read each Row
    #             for row in rdr:
    #                 if (row and str(row[0]) > 0):
    #                     row = striplist(row)
    #                     try:
    #                         accountcode = ''
    #                         # extra fields to import
    #                         caller_id_name = ''
    #                         direction = 'outbound'
    #                         remote_media_ip = ''
    #                         answer_uepoch = ''
    #                         end_uepoch = ''
    #                         mduration = ''
    #                         billmsec = ''
    #                         write_codec = ''
    #                         read_codec = ''
    #                         get_cdr_from_row = {}
    #                         row_counter = 0

    #                         for j in uni:
    #                             get_cdr_from_row[j[0]] = row[j[1] - 1]
    #                             #get_cdr_from_row[j[0]] = row[row_counter]
    #                             caller_id_name = get_value_from_uni(j, row, 'caller_id_name')
    #                             caller_id_number = get_value_from_uni(j, row, 'caller_id_number')
    #                             direction = get_value_from_uni(j, row, 'direction')
    #                             remote_media_ip = get_value_from_uni(j, row, 'remote_media_ip')
    #                             answer_uepoch = get_value_from_uni(j, row, 'answer_uepoch')
    #                             end_uepoch = get_value_from_uni(j, row, 'end_uepoch')
    #                             mduration = get_value_from_uni(j, row, 'mduration')
    #                             billmsec = get_value_from_uni(j, row, 'billmsec')
    #                             read_codec = get_value_from_uni(j, row, 'read_codec')
    #                             write_codec = get_value_from_uni(j, row, 'write_codec')
    #                             row_counter = row_counter + 1

    #                         if len(field_notin_list) != 0:
    #                             for i in field_notin_list:
    #                                 if i == 'accountcode' and request.POST.get("accountcode_csv"):
    #                                     accountcode = request.POST["accountcode_csv"]

    #                         if not accountcode and request.POST.get("accountcode") != '0':
    #                             accountcode = get_cdr_from_row['accountcode']

    #                         # Mandatory fields to import
    #                         switch_id = int(request.POST['switch_id'])
    #                         caller_id_number = get_cdr_from_row['caller_id_number']
    #                         duration = int(get_cdr_from_row['duration'])
    #                         billsec = int(get_cdr_from_row['billsec'])

    #                         if (request.POST.get('import_asterisk')
    #                            and request.POST['import_asterisk'] == 'on'):
    #                             hangup_cause_name = "_".join(get_cdr_from_row['hangup_cause_id'].upper().split(' '))
    #                             hangup_cause_id = get_hangupcause_id_from_name(hangup_cause_name)
    #                         else:
    #                             hangup_cause_id = get_hangupcause_id(int(get_cdr_from_row['hangup_cause_id']))

    #                         start_uepoch = datetime.datetime.fromtimestamp(int(float(get_cdr_from_row['start_uepoch'])))

    #                         destination_number = get_cdr_from_row['destination_number']
    #                         uuid = get_cdr_from_row['uuid']

    #                         destination_data = chk_destination(destination_number)
    #                         authorized = destination_data['authorized']
    #                         country_id = destination_data['country_id']

    #                         # Extra fields to import
    #                         if answer_uepoch:
    #                             answer_uepoch = datetime.datetime.fromtimestamp(int(answer_uepoch[:10]))
    #                         if end_uepoch:
    #                             end_uepoch = datetime.datetime.fromtimestamp(int(end_uepoch[:10]))

    #                         # Prepare global CDR
    #                         cdr_record = generate_global_cdr_record(switch_id, caller_id_number,
    #                             caller_id_name, destination_number, duration, billsec, hangup_cause_id,
    #                             accountcode, direction, uuid, remote_media_ip, start_uepoch, answer_uepoch,
    #                             end_uepoch, mduration, billmsec, read_codec, write_codec,
    #                             CDR_SOURCE_TYPE.CSV, '', country_id, authorized)

    #                         # check if cdr is already existing in cdr_common
    #                         if not mongodb.cdr_common:
    #                             raise Http404
    #                         mongodb.cdr_common = settings.DBCON[settings.MONGO_CDRSTATS['CDR_COMMON']]
    #                         query_var = {}
    #                         query_var['uuid'] = uuid
    #                         record_count = mongodb.cdr_common.find(query_var).count()

    #                         if record_count >= 1:
    #                             msg = _('CDR already exists !!')
    #                             error_import_list.append(row)
    #                         else:
    #                             # if not, insert record
    #                             # record global CDR

    #                             # Append cdr to bulk_cdr list
    #                             cdr_bulk_record.append(cdr_record)

    #                             local_count_import = local_count_import + 1
    #                             if local_count_import == PAGE_SIZE:
    #                                 mongodb.cdr_common.insert(cdr_bulk_record)
    #                                 local_count_import = 0
    #                                 cdr_bulk_record = []

    #                             date_start_uepoch = get_cdr_from_row['start_uepoch']
    #                             create_analytic(date_start_uepoch, start_uepoch,
    #                                             switch_id, country_id, accountcode,
    #                                             hangup_cause_id, duration)

    #                             cdr_record_count = cdr_record_count + 1

    #                             msg = _('%(cdr_record_count)s CDR(s) are uploaded, out of %(total_rows)s row(s) !!')\
    #                                 % {'cdr_record_count': cdr_record_count,
    #                                    'total_rows': total_rows}
    #                             success_import_list.append(row)
    #                     except:
    #                         msg = _("error : invalid value for import")
    #                         type_error_import_list.append(row)

    #             # remaining record
    #             if cdr_bulk_record:
    #                 mongodb.cdr_common.insert(cdr_bulk_record)
    #                 local_count_import = 0
    #                 cdr_bulk_record = []

    #             if cdr_record_count > 0:
    #                 # Apply index
    #                 apply_index(shell=True)
    #         else:
    #             msg = _("error : importing several times the same column")

    #     ctx = RequestContext(request, {
    #         'title': _('import CDR'),
    #         'form': form,
    #         'opts': opts,
    #         'model_name': opts.object_name.lower(),
    #         'app_label': app_label,
    #         'rdr': rdr,
    #         'msg': msg,
    #         'success_import_list': success_import_list,
    #         'error_import_list': error_import_list,
    #         'type_error_import_list': type_error_import_list,
    #         'CDR_FIELD_LIST': list(CDR_FIELD_LIST),
    #         'CDR_FIELD_LIST_NUM': list(CDR_FIELD_LIST_NUM),
    #     })
    #     return render_to_response('admin/cdr/switch/import_cdr.html', context_instance=ctx)

    # def cdr_view(self, request):
    #     """List of CDRs

    #     **Attributes**:

    #         * ``template`` - admin/voip_billing/voipplan/cdr_view.html
    #         * ``form`` - CdrSearchForm
    #         * ``mongodb_data_set`` - mongodb.cdr_common

    #     **Logic Description**:

    #         get the call records as well as daily call analytics
    #         from mongodb collection according to search parameters
    #     """
    #     opts = Switch._meta
    #     logging.debug('CDR View Start')
    #     query_var = {}
    #     result = 1  # default min
    #     switch_id = 0  # default all
    #     hangup_cause_id = 0  # default all
    #     destination = ''
    #     destination_type = ''
    #     dst = ''
    #     accountcode = ''
    #     accountcode_type = ''
    #     acc = ''
    #     direction = ''
    #     duration = ''
    #     duration_type = ''
    #     due = ''
    #     caller = ''
    #     caller_type = ''
    #     cli = ''
    #     action = 'tabs-1'
    #     menu = 'on'
    #     cdr_view_daily_data = {}
    #     export_query_var = {}
    #     country_id = ''
    #     records_per_page = 10
    #     form = CdrSearchForm(request.POST or None)
    #     if form.is_valid():
    #         logging.debug('CDR Search View')

    #         # set session var value
    #         field_list = ['destination', 'result', 'destination_type', 'accountcode',
    #                       'accountcode_type', 'caller', 'caller_type', 'duration',
    #                       'duration_type', 'hangup_cause_id', 'switch_id', 'direction',
    #                       'country_id']
    #         unset_session_var(request, field_list)

    #         from_date = getvar(request, 'from_date', setsession=False)
    #         to_date = getvar(request, 'to_date', setsession=False)
    #         result = getvar(request, 'result', setsession=True)
    #         destination = getvar(request, 'destination', setsession=True)
    #         destination_type = getvar(request, 'destination_type', setsession=True)
    #         accountcode = getvar(request, 'accountcode', setsession=True)
    #         accountcode_type = getvar(request, 'accountcode_type', setsession=True)
    #         caller = getvar(request, 'caller', setsession=True)
    #         caller_type = getvar(request, 'caller_type', setsession=True)
    #         duration = getvar(request, 'duration', setsession=True)
    #         duration_type = getvar(request, 'duration_type', setsession=True)
    #         direction = getvar(request, 'direction', setsession=True)
    #         if direction and direction != 'all':
    #             request.session['session_direction'] = str(direction)
    #         switch_id = getvar(request, 'switch_id', setsession=True)
    #         hangup_cause_id = getvar(request, 'hangup_cause_id', setsession=True)
    #         records_per_page = getvar(request, 'records_per_page', setsession=True)

    #         country_id = form.cleaned_data.get('country_id')
    #         # convert list value in int
    #         country_id = [int(row) for row in country_id]
    #         if len(country_id) >= 1:
    #             request.session['session_country_id'] = country_id

    #         start_date = ceil_strdate(from_date, 'start', True)
    #         end_date = ceil_strdate(to_date, 'end', True)
    #         converted_start_date = start_date.strftime('%Y-%m-%d %H:%M')
    #         converted_end_date = end_date.strftime('%Y-%m-%d %H:%M')
    #         request.session['session_start_date'] = converted_start_date
    #         request.session['session_end_date'] = converted_end_date

    #     menu = 'off'

    #     if request.GET.get('page') or request.GET.get('sort_by'):
    #         from_date = start_date = request.session.get('session_start_date')
    #         to_date = end_date = request.session.get('session_end_date')
    #         start_date = ceil_strdate(start_date, 'start', True)
    #         end_date = ceil_strdate(end_date, 'end', True)
    #         destination = request.session.get('session_destination')
    #         destination_type = request.session.get('session_destination_type')
    #         accountcode = request.session.get('session_accountcode')
    #         accountcode_type = request.session.get('session_accountcode_type')
    #         caller = request.session.get('session_caller')
    #         caller_type = request.session.get('session_caller_type')
    #         duration = request.session.get('session_duration')
    #         duration_type = request.session.get('session_duration_type')
    #         direction = request.session.get('session_direction')
    #         switch_id = request.session.get('session_switch_id')
    #         hangup_cause_id = request.session.get('session_hangup_cause_id')
    #         result = int(request.session.get('session_result'))
    #         records_per_page = request.session.get('session_records_per_page')
    #         country_id = request.session['session_country_id']
    #         cdr_view_daily_data = request.session.get('session_cdr_view_daily_data')
    #     else:
    #         if request.method == 'GET':
    #             tday = datetime.today()
    #             from_date = datetime(tday.year, tday.month, 1, 0, 0, 0, 0)
    #             last_day = ((datetime(tday.year, tday.month, 1, 23, 59, 59, 999999) +
    #                         relativedelta(months=1)) -
    #                         relativedelta(days=1)).strftime('%d')
    #             #to_date = tday.strftime('%Y-%m-' + last_day + ' 23:59')
    #             to_date = datetime(tday.year, tday.month, int(last_day), 23, 59, 59, 999999)
    #             start_date = ceil_strdate(str(from_date), 'start', True)
    #             end_date = ceil_strdate(str(to_date), 'end', True)

    #             converted_start_date = start_date.strftime('%Y-%m-%d %H:%M')
    #             converted_end_date = end_date.strftime('%Y-%m-%d %H:%M')

    #             # unset session var value
    #             request.session['session_result'] = 1
    #             request.session['session_start_date'] = converted_start_date
    #             request.session['session_end_date'] = converted_end_date

    #             field_list = ['destination', 'destination_type', 'accountcode',
    #                           'accountcode_type', 'caller', 'caller_type', 'duration',
    #                           'duration_type', 'hangup_cause_id', 'switch_id', 'direction',
    #                           'country_id']
    #             unset_session_var(request, field_list)
    #             request.session['session_records_per_page'] = records_per_page
    #             request.session['session_country_id'] = ''

    #     query_var['start_uepoch'] = {'$gte': start_date, '$lt': end_date}

    #     # aggregate query variable
    #     daily_report_query_var = {}
    #     daily_report_query_var['metadata.date'] = {'$gte': start_date, '$lt': end_date}

    #     dst = mongodb_str_filter(destination, destination_type)
    #     if dst:
    #         query_var['destination_number'] = dst

    #     if request.user.is_superuser:
    #         # superuser can see everything
    #         acc = mongodb_str_filter(accountcode, accountcode_type)
    #         if acc:
    #             daily_report_query_var['metadata.accountcode'] = acc
    #             query_var['accountcode'] = acc

    #     if not request.user.is_superuser:
    #         daily_report_query_var['metadata.accountcode'] = request.user.userprofile.accountcode
    #         query_var['accountcode'] = daily_report_query_var['metadata.accountcode']

    #     cli = mongodb_str_filter(caller, caller_type)
    #     if cli:
    #         query_var['caller_id_number'] = cli

    #     due = mongodb_int_filter(duration, duration_type)
    #     if due:
    #         query_var['duration'] = daily_report_query_var['duration_daily'] = due

    #     if switch_id and int(switch_id) != 0:
    #         daily_report_query_var['metadata.switch_id'] = int(switch_id)
    #         query_var['switch_id'] = int(switch_id)

    #     if hangup_cause_id and int(hangup_cause_id) != 0:
    #         daily_report_query_var['metadata.hangup_cause_id'] = int(hangup_cause_id)
    #         query_var['hangup_cause_id'] = int(hangup_cause_id)

    #     if direction and direction != 'all':
    #         query_var['direction'] = str(direction)

    #     if len(country_id) >= 1 and country_id[0] != 0:
    #         daily_report_query_var['metadata.country_id'] = {'$in': country_id}
    #         query_var['country_id'] = {'$in': country_id}

    #     # store query_var in session without date
    #     export_query_var = query_var.copy()
    #     del export_query_var['start_uepoch']
    #     request.session['session_export_query_var'] = export_query_var

    #     final_result = mongodb.cdr_common.find(query_var,
    #         {
    #             "uuid": 0,
    #             "answer_uepoch": 0,
    #             "end_uepoch": 0,
    #             "mduration": 0,
    #             "billmsec": 0,
    #             "read_codec": 0,
    #             "write_codec": 0,
    #             "remote_media_ip": 0,
    #         }
    #     )

    #     form = CdrSearchForm(
    #         initial={
    #             'from_date': from_date,
    #             'to_date': to_date,
    #             'destination': destination,
    #             'destination_type': destination_type,
    #             'accountcode': accountcode,
    #             'accountcode_type': accountcode_type,
    #             'caller': caller,
    #             'caller_type': caller_type,
    #             'duration': duration,
    #             'duration_type': duration_type,
    #             'result': result,
    #             'direction': direction,
    #             'hangup_cause_id': hangup_cause_id,
    #             'switch_id': switch_id,
    #             'country_id': country_id,
    #             'records_per_page': records_per_page
    #         }
    #     )

    #     # Define no of records per page
    #     records_per_page = int(records_per_page)
    #     page_data = get_pagination_vars(request)

    #     logging.debug('Create cdr result')
    #     SKIP_NO = records_per_page * (page_data['PAGE_NUMBER'] - 1)
    #     record_count = final_result.count()
    #     rows = final_result.skip(SKIP_NO).limit(records_per_page).sort([(page_data['sort_field'], page_data['default_order'])])

    #     # Get daily report from session while using pagination & sorting
    #     cdr_view_daily_data = cdr_view_daily_report(daily_report_query_var)

    #     template_data = RequestContext(request, {
    #         'rows': rows,
    #         'form': form,
    #         'record_count': record_count,
    #         'cdr_daily_data': cdr_view_daily_data,
    #         'col_name_with_order': page_data['col_name_with_order'],
    #         'menu': menu,
    #         'start_date': start_date,
    #         'end_date': end_date,
    #         'action': action,
    #         'result': int(result),
    #         'CDR_COLUMN_NAME': CDR_COLUMN_NAME,
    #         'opts': opts,
    #         'model_name': opts.object_name.lower(),
    #         'app_label': APP_LABEL,
    #         'records_per_page': records_per_page,
    #         'sort_up': '<i class="fa fa-sort-up"></i>',
    #         'sort_down': '<i class="fa fa-sort-down"></i>',
    #     })
    #     logging.debug('CDR View End')
    #     return render_to_response('admin/cdr/switch/cdr_view.html', context_instance=template_data)

    # def export_cdr(self, request):
    #     # get the response object, this can be used as a stream.
    #     format_type = request.GET['format']
    #     response = HttpResponse(mimetype='text/%s' % format_type)
    #     # force download.
    #     response['Content-Disposition'] = 'attachment;filename=export.%s' % format_type

    #     # super(VoIPCall_ReportAdmin, self).queryset(request)
    #     export_query_var = request.session.get('session_export_query_var')
    #     start_date = request.session.get('session_start_date')
    #     end_date = request.session.get('session_end_date')
    #     start_date = ceil_strdate(start_date, 'start', True)
    #     end_date = ceil_strdate(end_date, 'end', True)
    #     export_query_var["start_uepoch"] = {"$gte": start_date, "$lt": end_date}

    #     final_result = mongodb.cdr_common.find(export_query_var,
    #         {
    #             "uuid": 0,
    #             "answer_uepoch": 0,
    #             "end_uepoch": 0,
    #             "mduration": 0,
    #             "billmsec": 0,
    #             "read_codec": 0,
    #             "write_codec": 0,
    #             "remote_media_ip": 0
    #         }
    #     )

    #     headers = ('Call-date', 'CLID', 'Destination', 'Duration',
    #                'Bill sec', 'Hangup cause', 'AccountCode', 'Direction')

    #     list_val = []

    #     for cdr in final_result:
    #         starting_date = cdr['start_uepoch']
    #         if format_type == 'json':
    #             starting_date = str(cdr['start_uepoch'])

    #         list_val.append((
    #             starting_date,
    #             cdr['caller_id_number'] + '-' + cdr['caller_id_name'],
    #             cdr['destination_number'],
    #             cdr['duration'],
    #             cdr['billsec'],
    #             get_hangupcause_name(cdr['hangup_cause_id']),
    #             cdr['accountcode'],
    #             cdr['direction'],
    #         ))
    #     data = tablib.Dataset(*list_val, headers=headers)

    #     if format_type == Export_choice.XLS:
    #         response.write(data.xls)
    #     elif format_type == Export_choice.CSV:
    #         response.write(data.csv)
    #     elif format_type == Export_choice.JSON:
    #         response.write(data.json)
    #     return response

admin.site.register(Switch, SwitchAdmin)
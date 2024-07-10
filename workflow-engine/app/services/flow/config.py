# -*- coding:utf-8 -*-

from collections import OrderedDict

from app.services.flow.workflow_template_service import WorkflowTemplateService


class Config(object):

    flow = dict()
    type_list = [e for e in WorkflowTemplateService.list_template_type()]
    for template_type in type_list:
        one_flow = OrderedDict()
        template_data = WorkflowTemplateService.list_template(template_type)
        for t in template_data:
            one_flow[t.get('key')] = t
        flow[template_type] = one_flow

    @staticmethod
    def reload_config(template_type):
        one_flow = OrderedDict()
        template_data = WorkflowTemplateService.list_template(template_type)
        for t in template_data:
            one_flow[t.get('key')] = t
        Config.flow[template_type] = one_flow

    @staticmethod
    def get_task_type_name(flow_type, task_type):
        return Config.flow.get(flow_type).get(task_type).get('name')

    @staticmethod
    def get_flow_info(flow_type, task_name):
        if Config.flow.get(flow_type):
            return Config.flow.get(flow_type).get(task_name)

    @staticmethod
    def get_flow_svg(flow_type, current_task_type):
        flow = Config.flow.get(flow_type)
        graph = dict()
        graph['cross'] = list()
        result = list()
        i = 0
        while i < len(flow.items()) - 1:
            k = flow.items()[i][0]
            v = flow.items()[i][1]
            if not v.get('env') in graph.keys():
                graph[v.get('env')] = list()
            if 'directions' not in v.keys():
                graph[v.get('env')].append(k + "(" + Config.get_task_type_name(flow_type, k) + ")")
            if 'directions' in v.keys():
                for dk, dv in v.get('directions').items():
                    nk = dv.get('go')
                    dn = dv.get('name')
                    if v.get('env') == flow.get(nk).get('env'):
                        graph[v.get('env')].append(k + "(" + Config.get_task_type_name(flow_type, k) + ")-->|"+dn+"|"+nk + "(" + Config.get_task_type_name(flow_type, nk) + ")")
                    else:
                        graph['cross'].append(k + "(" + Config.get_task_type_name(flow_type, k) + ")-->|"+dn+"|"+nk + "(" + Config.get_task_type_name(flow_type, nk) + ")")
            i += 1
        for vi in graph.pop('cross'):
            result.append(vi)
        for k, v in graph.items():
            result.append('subgraph {}'.format(k))
            for vi in v:
                result.append(vi)
            result.append('end')
        if current_task_type:
            result.append("style " + current_task_type + " fill:#F8EB16,stroke:#3333FF,stroke-width:2px;")
        return result

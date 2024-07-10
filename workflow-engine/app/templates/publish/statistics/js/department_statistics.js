var dept_data = new Vue({
    el: '#tab2',
    data:{
        begin_date: '',
        end_date: '',
        selected_department: '',
        department_label: '',
        department_list: [],
        total: 0,
        dept_publish_records: [],
        owner_publish_records: []
    },
    methods:{
        filter: function(){
            this.begin_date = $('#dept_begin_date input').val(),
            this.end_date = $('#dept_end_date input').val()
            for(i=0;i<this.department_list.length;i++){
                if(this.department_list[i].value==this.selected_department){
                    this.department_label = this.department_list[i].label
                    break
                }
            }
            this.load_publish_records_by_department()
            this.load_publish_records_by_owners()
        },
        export_data: function(type){
            if(type=='all'){
                window.location.href="{{url_for('publishStatisticsProfile.export_publish_statistics')}}?type="+type+"&begin_date="+$('#dept_begin_date input').val()+"&end_date="+$('#dept_end_date input').val()+"&group=department"+"&query="+this.department_label
            }else{
                window.location.href="{{url_for('publishStatisticsProfile.export_publish_statistics')}}?type="+type+"&begin_date="+$('#dept_begin_date input').val()+"&end_date="+$('#dept_end_date input').val()+"&query="+this.department_label+"&query_by=department"
            }
        },
        load_app_department: function() {
            this.$http.get("{{config['APPREPO_URL']}}/api/app/department/list", {params: {"company_id":1, "r":Math.random()}, emulateJSON: true}).then(
                function(response){
                    this.department_list = [];
                    if(response.data.result == 1){
                        this.department_list = response.data.data.departmentList;
                    }
                },function(res){
                    errorModal.msg='网络连接异常，请稍后重试。';
                    errorModal.show=true;
                });
         },
        load_publish_records_by_department: function(){
            this.$http.get("{{url_for('publishStatisticsProfile.get_publish_statistics')}}", {params: {"begin_date": $('#dept_begin_date input').val(), "end_date": $('#dept_end_date input').val(), "query": this.department_label, "group": "department"}, emulateJSON: true}).then(
                function(response){
                    if(response.data.result == 1){
                        this.dept_publish_records = response.data.data
                        this.total = response.data.total
                    }
                },function(res){
                    errorModal.msg='网络连接异常，请稍后重试。';
                    errorModal.show=true;
                });
        },
        load_publish_records_by_owners: function(){
            this.$http.get("{{url_for('publishStatisticsProfile.get_publish_statistics_by_owner')}}", {params: {"begin_date": $('#dept_begin_date input').val(), "end_date": $('#dept_end_date input').val(), "query_by": "department", "query": this.department_label}, emulateJSON: true}).then(
                function(response){
                    if(response.data.result == 1){
                        this.owner_publish_records = response.data.data.owner_record
                    }
                },function(res){
                    errorModal.msg='网络连接异常，请稍后重试。';
                    errorModal.show=true;
                });
        }
    }
});
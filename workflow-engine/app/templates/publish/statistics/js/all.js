var all = new Vue({
    el: '#tab1',
    data:{
        begin_date: '',
        end_date: '',
        total: 0,
        publish_records: [],
        pre_rollback_records: {},
        owner_rollback_records: {},
        project_abandon_records: []
    },
    methods:{
        filter: function(){
            this.begin_date = $('#begin_date input').val(),
            this.end_date = $('#end_date input').val()
            this.load_publish_records_by_production()
            this.load_abandon_records()
            this.load_abandon_records_top_10()
        },
        export_data: function(type){
            if(type=='all'){
                window.location.href="{{url_for('publishStatisticsProfile.export_publish_statistics')}}?type="+type+"&begin_date="+$('#begin_date input').val()+"&end_date="+$('#end_date input').val()+"&group=department, system"
            }else{
                window.location.href="{{url_for('publishStatisticsProfile.export_publish_statistics')}}?type="+type+"&begin_date="+$('#begin_date input').val()+"&end_date="+$('#end_date input').val()
            }

        },
        load_publish_records_by_production: function(){
            this.$http.get("{{url_for('publishStatisticsProfile.get_publish_statistics')}}", {params: {"begin_date": this.begin_date, "end_date": this.end_date, "group": "department, system"}, emulateJSON: true}).then(
                function(response){
                    if(response.data.result == 1){
                        this.publish_records = response.data.data
                        this.total = response.data.total
                    }
                },function(res){
                    errorModal.msg='网络连接异常，请稍后重试。';
                    errorModal.show=true;
                });
        },
        load_abandon_records: function(){
             this.$http.get("{{url_for('publishStatisticsProfile.get_publish_abandon_statistics')}}", {params: {"begin_date": this.begin_date, "end_date": this.end_date}, emulateJSON: true}).then(
                function(response){
                    if(response.data.result == 1){
                        this.owner_rollback_records = {}
                        this.pre_rollback_records = {}
                        var rollback_records = response.data.data
                        for(k in rollback_records){
                            if(k=='owner_rollback_reason'){
                                for(key in rollback_records['owner_rollback_reason']){
                                    this.owner_rollback_records[key] = rollback_records['owner_rollback_reason'][key]
                                 }
                            }else{
                                for(key in rollback_records['pre_not_pass_reason']){
                                    this.pre_rollback_records[key] = rollback_records['pre_not_pass_reason'][key]
                                }
                            }
                        }
                    }
                },function(res){
                    errorModal.msg='网络连接异常，请稍后重试。';
                    errorModal.show=true;
                });
        },
        load_abandon_records_top_10: function(){
             this.$http.get("{{url_for('publishStatisticsProfile.get_publish_abandon_statistics_top10')}}", {params: {"begin_date": this.begin_date, "end_date": this.end_date}, emulateJSON: true}).then(
                function(response){
                    if(response.data.result == 1){
                        this.project_abandon_records = response.data.data
                    }
                },function(res){
                    errorModal.msg='网络连接异常，请稍后重试。';
                    errorModal.show=true;
                });
        }
    }
});
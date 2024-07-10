var owner_data = new Vue({
    el: '#tab3',
    data:{
        begin_date: '',
        end_date: '',
        selected_owner: '',
        owner_list: [],
        owner_name: '',
        total: 0,
        product_publish_records: [],
        owner_publish_records: []
    },
    methods:{
        filter: function(){
            this.begin_date = $('#owner_begin_date input').val(),
            this.end_date = $('#owner_end_date input').val()
            this.selected_owner = $('#owner').val()
            for(i=0;i<this.owner_list.length;i++){
                if(this.owner_list[i].name==this.selected_owner){
                    this.owner_name = this.owner_list[i].real_name
                    break
                }
            }
            this.load_publish_records_by_owners()

        },
         export_data: function(type){
            window.location.href="{{url_for('publishStatisticsProfile.export_publish_statistics')}}?type="+type+"&begin_date="+$('#owner_begin_date input').val()+"&end_date="+$('#owner_end_date input').val()+"&query="+this.owner_name+"&query_by=owner"
        },
        load_users: function() {
            owner_data.owner_list = []
            this.$http.get("{{url_for('publishStatisticsProfile.get_project_owners')}}", {params: {"begin_date": owner_data.begin_date, "end_date": owner_data.end_date}, emulateJSON: true}).then(
                function(response){
                    if(response.data.result == 1){
                        owner_data.owner_list = response.data.data;
                    }
                },function(res){
                    errorModal.msg='网络连接异常，请稍后重试。';
                    errorModal.show=true;
                });
         },
        load_publish_records_by_owners: function(){
            this.owner_publish_records = []
            this.$http.get("{{url_for('publishStatisticsProfile.get_publish_statistics_by_owner')}}", {params: {"begin_date": $('#owner_begin_date input').val(), "end_date": $('#owner_end_date input').val(), "query_by": "owner", "query": this.owner_name}, emulateJSON: true}).then(
                function(response){
                    if(response.data.result == 1){
                        this.owner_publish_records.push(response.data.data.owner_record)
                        this.product_publish_records = response.data.data.owner_product_record
                        this.total = response.data.data.total
                    }
                },function(res){
                    errorModal.msg='网络连接异常，请稍后重试。';
                    errorModal.show=true;
                });
        }
    }
});
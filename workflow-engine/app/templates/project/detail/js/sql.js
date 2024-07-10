var newSQLModal = new Vue({
    el: "#newSQLModal",
    data: {
        show: false,
    },
    methods: {
        commit: function(){
            var env_execution_config = {"company_id":basic.selected_company, "sql_execute_config":{"pre": {"execution_before": $('#pre_before').prop("checked"), "execution_after": $('#pre_after').prop("checked")}, "prd": {"execution_before": $('#prd_before').prop("checked"), "execution_after": $('#prd_after').prop("checked")}}}
            newSQLModal.show = false
            this.$http.post("{{url_for('projectProfile.add_sql_review', project_id=project_id)}}", env_execution_config).then(
                function(response){
                    if(response.data.result == 1){
                        sqlreview.load_sql_review()
                    }else{
                        errorModal.msg=response.data.message;
                        errorModal.show=true;
                    }
                },function(res){
                    errorModal.msg='网络连接异常，请稍后重试。';
                    errorModal.show=true;
                });
            return
        },
        close: function(){
            newSQLModal.show = false
            newSQLModal.show_aut = false
        }
    }
})

var editSQLModal = new Vue({
    el: "#editSQLModal",
    data: {
        show: false
    },
    methods: {
        commit: function(){
            var env_execution_config = {"aut": {"execution_before": $('#edit_aut_before').prop("checked"), "execution_after": $('#edit_aut_after').prop("checked")}, "pre": {"execution_before": $('#edit_pre_before').prop("checked"), "execution_after": $('#edit_pre_after').prop("checked")}, "prd": {"execution_before": $('#edit_prd_before').prop("checked"), "execution_after": $('#edit_prd_after').prop("checked")}}

            editSQLModal.show = false
            this.$http.post("{{url_for('projectProfile.mod_sql_review', project_id=project_id)}}", env_execution_config).then(
                function(response){
                    if(response.data.result == 1){
                        sqlreview.load_sql_review()
                    }else{
                        errorModal.msg=response.data.message;
                        errorModal.show=true;
                    }
                },function(res){
                    errorModal.msg='网络连接异常，请稍后重试。';
                    errorModal.show=true;
                });
        },
        close: function(){
            editSQLModal.show = false
        }
    }
})
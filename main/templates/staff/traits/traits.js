axios.defaults.xsrfHeaderName = "X-CSRFTOKEN";
axios.defaults.xsrfCookieName = "csrftoken";

var app = Vue.createApp({

    delimiters: ['[[', ']]'],
       
    data(){return{
        //sessions:[],
        file: '',
        file_name:'Choose File',
        upload_messaage:'',
        download_messaage:'',
        upload_button_text:'Upload <i class="fas fa-upload"></i>',
        download_button_text:'Generate <i class="fas fa-scroll fa-xs"></i>',
        active_only:true,
        select_all_value:true,
        include_sign_up_metrics:false,
        session_day:{{session_day|safe}},
    }},

    methods:{
        uploadCSV:function(){

            if(app.$data.file == "")
                return;

            app.$data.upload_messaage = "";
            app.$data.upload_button_text = '<i class="fas fa-spinner fa-spin"></i>';

            let formData = new FormData();
            formData.append('file', app.$data.file);

            axios.post('/traits/', formData,
                    {
                        headers: {
                            'Content-Type': 'multipart/form-data'
                            }
                        } 
                    )
                    .then(function (response) {     

                        app.$data.upload_messaage = response.data.message;
                        app.$data.upload_button_text= 'Upload <i class="fas fa-upload"></i>'
                                                                        
                    })
                    .catch(function (error) {
                        console.log(error);
                        app.$data.searching=false;
                    });                        
                },
        
        handleFileUpload:function(){
            app.$data.file = this.$refs.file.files[0];
            app.$data.file_name = app.$data.file.name;
        },
        
        getReport:function(){
            app.$data.download_messaage = "";
            app.$data.download_button_text = '<i class="fas fa-spinner fa-spin"></i>';

            axios.post('/traits/', {
                        action :"getReport",  
                        formData : $("#traitReportForm").serializeArray(),    
                        active_only:app.$data.active_only,       
                        include_sign_up_metrics : app.$data.include_sign_up_metrics,   
                        session_day : app.$data.session_day,                                                                                                             
                    })
                    .then(function (response) {    
                        
                        status=response.data.status;                                                                  

                        //app.clearMainFormErrors();

                        if(status=="fail")
                        {                         
                            //app.displayErrors(response.data.errors);             
                        }
                        else
                        {                                                                       
                            // console.log(response.data);

                            var downloadLink = document.createElement("a");
                            var blob = new Blob(["\ufeff", response.data]);
                            var url = URL.createObjectURL(blob);
                            downloadLink.href = url;
                            downloadLink.download = "Traits_Report.csv";

                            document.body.appendChild(downloadLink);
                            downloadLink.click();
                            document.body.removeChild(downloadLink);
                        }
                     
                        app.$data.download_button_text = 'Generate <i class="fas fa-scroll fa-xs"></i>';
                    })
                    .catch(function (error) {
                        console.log(error);
                        app.$data.searching=false;
                    });                        
                },
        
        //select all traits
        selectAll:function(){
            checkboxes = document.getElementsByName('traits');

            for(var i=0, n=checkboxes.length;i<n;i++) {
                checkboxes[i].checked = app.$data.select_all_value;
            }

            app.$data.select_all_value = !app.$data.select_all_value;
        },
    },


    mounted(){
            //this.getUser();                    
    },
}).mount('#app');

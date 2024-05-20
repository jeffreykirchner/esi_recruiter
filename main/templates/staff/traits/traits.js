"use strict";

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
        selected_traits:[],
        session_day:{{session_day|safe}},
    }},

    methods:{
        uploadCSV:function uploadCSV(){

            if(app.file == "")
                return;

            app.upload_messaage = "";
            app.upload_button_text = '<i class="fas fa-spinner fa-spin"></i>';

            let formData = new FormData();
            formData.append('file', app.file);

            axios.post('/traits/', formData,
                    {
                        headers: {
                            'Content-Type': 'multipart/form-data'
                            }
                        } 
                    )
                    .then(function (response) {     

                        app.upload_messaage = response.data.message;
                        app.upload_button_text= 'Upload <i class="fas fa-upload"></i>'
                                                                        
                    })
                    .catch(function (error) {
                        console.log(error);
                        app.searching=false;
                    });                        
                },
        
        handleFileUpload:function handleFileUpload(){
            app.file = this.$refs.file.files[0];
            app.file_name = app.file.name;
        },
        
        getReport:function getReport(){
            app.download_messaage = "";
            app.download_button_text = '<i class="fas fa-spinner fa-spin"></i>';

            axios.post('/traits/', {
                        action :"getReport",  
                        formData : {"traits":app.selected_traits},    
                        active_only:app.active_only,       
                        include_sign_up_metrics : app.include_sign_up_metrics,   
                        session_day : app.session_day,                                                                                                             
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
                     
                        app.download_button_text = 'Generate <i class="fas fa-scroll fa-xs"></i>';
                    })
                    .catch(function (error) {
                        console.log(error);
                        app.searching=false;
                    });                        
                },
        
        //select all traits
        selectAll:function selectAll(){
            checkboxes = document.getElementsByName('traits');

            for(var i=0, n=checkboxes.length;i<n;i++) {
                checkboxes[i].checked = app.select_all_value;
            }

            app.select_all_value = !app.select_all_value;
        },
    },


    mounted(){
            //this.getUser();                    
    },
}).mount('#app');

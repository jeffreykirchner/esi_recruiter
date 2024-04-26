axios.defaults.xsrfHeaderName = "X-CSRFTOKEN";
axios.defaults.xsrfCookieName = "csrftoken";

var app = Vue.createApp({
    delimiters: ['[[', ']]'],
   
    data() {return{
        baseURL:'{{request.get_full_path}}',                                                                                                                 
        users:[],      
        searchInfo:"", 
        warningText:"",
        searchButtonText:'Search <i class="fas fa-search"></i>',
        blackBallButtonText : 'Blackballs',
        noShowButtonText : 'No-Show Blocks',
        activeOnly:true,
        searchCount:0,                        //user found during search
        sendMessageButtonText:"Send Message <i class='fas fa-envelope fa-xs'></i>",         //send message button text
        sendMessageSubject:"",               //subject of send message     
        sendMessageText:"[first name],<br><br><br>[contact email]",          //text of send message     
        emailMessageList:"",                 //emails for send message
        uploadInternationalText : "",
        uploadInternationalButtonText : 'Upload <i class="fa fa-upload" aria-hidden="true"></i>',
        uploadInternationalMessage : "",

        //modals
        sendMessageModalCenter:null,
        uploadInternationalModal:null,
    }},

    methods:{
        do_first_load:function do_first_load(){
            tinyMCE.init({
                target: document.getElementById('id_sendMessageText'),
                height : "400",
                theme: "silver",
                convert_urls: false,
                promotion: false,
                auto_focus: 'id_sendMessageText',
                plugins: "directionality,searchreplace,code,link",
                    toolbar: "undo redo | styleselect | forecolor | bold italic | alignleft aligncenter alignright alignjustify | outdent indent | link | code",
                directionality: "{{ directionality }}",
            });
    
            // Prevent Bootstrap dialog from blocking focusin
            document.addEventListener('focusin', (e) => {
                if (e.target.closest(".tox-tinymce-aux, .moxman-window, .tam-assetmanager-root") !== null) {
                    e.stopImmediatePropagation();
                }
            });

            app.sendMessageModalCenter = bootstrap.Modal.getOrCreateInstance(document.getElementById('sendMessageModalCenter'), {keyboard: false});
            app.uploadInternationalModal = bootstrap.Modal.getOrCreateInstance(document.getElementById('uploadInternationalModal'), {keyboard: false});
        },

        //get list of users based on search
        getUsers: function getUsers(){
            if(app.searchButtonText == '<i class="fas fa-spinner fa-spin"></i>') return;

            app.searchButtonText = '<i class="fas fa-spinner fa-spin"></i>';

            axios.post('{{request.get_full_path}}', {                            
                action:"getUsers",
                searchInfo:app.searchInfo,
                activeOnly:app.activeOnly,                                
            })
            .then(function (response) {                         
                app.functionTakeUserList(response);
                app.searchButtonText = 'Search <i class="fas fa-search"></i>';
            })
            .catch(function (error) {
                console.log(error);                               
            }); 
        }, 

        //get all active black balls
        getBlackballs: function getBlackballs(){
            if(app.blackBallButtonText == '<i class="fas fa-spinner fa-spin"></i>') return;

            app.blackBallButtonText = '<i class="fas fa-spinner fa-spin"></i>';

            axios.post('{{request.get_full_path}}', {                            
                action:"getBlackBalls",
                activeOnly:app.activeOnly,                                
            })
            .then(function (response) {                         
                app.functionTakeUserList(response);
                app.blackBallButtonText = 'Blackballs';
            })
            .catch(function (error) {
                console.log(error);                               
            }); 
        },

        //get all no show violators    
        getNoShowBlocks: function getNoShowBlocks(){
            if(app.noShowButtonText == '<i class="fas fa-spinner fa-spin"></i>') return;

            app.users = []
            app.warningText = "";
            app.noShowButtonText = '<i class="fas fa-spinner fa-spin"></i>';

            axios.post('{{request.get_full_path}}', {                            
                action:"getNoShows",
                activeOnly:app.activeOnly,                                
            })
            .then(function (response) {                         
                app.functionTakeUserList(response);
                app.noShowButtonText = 'No-Show Blocks';
            })
            .catch(function (error) {
                console.log(error);                               
            }); 
        },    

        //process incoming user list
        functionTakeUserList:function functionTakeUserList(response){
            if(response.data.errorMessage != "")
            {
                app.warningText = "Error: " + response.data.errorMessage;
                app.users = [];
            }
            else
            {
                app.users=JSON.parse(response.data.users);

                if(app.users.length == 0)
                {
                    app.warningText="No users found."
                }
                else
                {
                    app.warningText="";
                }

                app.searchCount = app.users.length;
            }                           
        },      
        
        //show international upload
        showInternational:function showInternational()
        {
            app.uploadInternationalModal.show();
        },

        //send international upload
        sendInternational:function sendInternational()
        {
            if(app.uploadInternationalButtonText == '<i class="fas fa-spinner fa-spin"></i>') return;

            app.uploadInternationalButtonText = '<i class="fas fa-spinner fa-spin"></i>';

            axios.post('{{request.get_full_path}}', {
                action:"sendInternational", 
                subject_list:app.uploadInternationalText,
                                                                                                                                             
            })
            .then(function (response) {
                //status=response.data.status;
                app.uploadInternationalModal.hide();

                app.functionTakeUserList(response);

                app.uploadInternationalButtonText = 'Upload <i class="fa fa-upload" aria-hidden="true"></i>';   
                                                                          
            })
            .catch(function (error) {
                console.log(error);
                //app.searching=false;                                                              
            });
        },

        // fire when invite subjects subjects model is shown
        showSendMessage:function showSendMessage(id){    
            tinymce.get("id_sendMessageText").setContent(this.sendMessageText);
            app.sendMessageModalCenter.show();                       
        },

        //fire when hide invite subjects  model, cancel action if nessicary
        hideSendMessage:function hideSendMessage(){ 
            if(app.sendMessageButtonText == "Send Message <i class='fas fa-envelope fa-xs'></i>")
            {
                app.sendMessageText="";      
                app.emailMessageList="";    
                app.sendMessageSubject="";  
            }      
                    
        },

        //send an email to all of the confirmed subjects
        sendEmailMessage:function sendEmailMessage(){

            if(app.sendMessageSubject == "" )
            {
                confirm("Add a subject to your message.");
                return;
            }

            if(app.sendMessageText == "" )
            {
                confirm("Your message is empty.");
                return;
            }

            app.sendMessageText = tinymce.get("id_sendMessageText").getContent();

            if(app.sendMessageButtonText == '<i class="fas fa-spinner fa-spin"></i>') return;

            app.sendMessageButtonText = '<i class="fas fa-spinner fa-spin"></i>';

            axios.post('{{request.get_full_path}}', {
                    action:"sendEmail", 
                    subject:app.sendMessageSubject,
                    text:app.sendMessageText,                                                                                                                                              
                })
                .then(function (response) {
                    //status=response.data.status;

                    if(response.data.mailResult.error_message != "")
                    {
                        app.emailMessageList = "<br>Email Send Error:<br>"
                        app.emailMessageList += response.data.mailResult.error_message + "<br><br>";
                    }
                    else
                    {
                        app.emailMessageList =  response.data.mailResult.mail_count + " messages sent.";                                     
                    }   

                    app.sendMessageButtonText = "Send Message <i class='fas fa-envelope fa-xs'></i>";                                                              
                })
                .catch(function (error) {
                    console.log(error);
                    //app.searching=false;                                                              
                });
            },

        formatDate: function formatDate(value){
                if (value) {
                    //return value;
                    return moment(String(value)).local().format('M/D/YYYY, h:mm a')
                }
                else{
                    return "date format error";
                }
            },           
        
    },
    
    mounted(){
       

        Vue.nextTick(() => {
            this.do_first_load();
        });

        setTimeout(() => {
            Vue.nextTick(() => {
                document.getElementById("idsearchInfo").focus();
            });
        }, 500);     
    },
}).mount('#app');
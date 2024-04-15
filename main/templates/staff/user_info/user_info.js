axios.defaults.xsrfHeaderName = "X-CSRFTOKEN";
axios.defaults.xsrfCookieName = "csrftoken";

var app = Vue.createApp({

    delimiters: ["[[", "]]"],
       
    data(){return{
        session_day_attended:[{id:"0"}],
        session_day_upcoming:[{id:"0"}],
        invitations:[{id:"0"}],
        institutions:[],
        subject_traits:[],
        notes:[],
        institutionsList:"",
        showInvitationsText:'Show <i class="fa fa-eye fa-xs"></i>',
        showTraitsButtonText:'Show <i class="fa fa-eye fa-xs"></i>',
        noInvitationsFoundText:'',
        noTraitsFoundText:'',
        noteText:'',
        working:true,
        subject:{},
        su:{%if user.is_staff%}true{%else%}false{%endif%},

        //modals
        noteModalCenter:null,
        editSubjectModal:null,
    }},

    methods:{
        //get attended and upcoming sessions
        getSessions:function(){
            axios.post('/userInfo/{{id}}/', {
                status :"getSessions" ,                                                                                                                             
            })
            .then(function (response) {     
                app.takeGetSessions(response);                    
            })
            .catch(function (error) {
                console.log(error);
                app.searching=false;
            });                        
        },

        //process get session response
        takeGetSessions:function(response)
        {
            app.session_day_attended = response.data.session_day_attended;
            app.session_day_upcoming = response.data.session_day_upcoming;  
            app.institutions = response.data.institutions;     
            app.notes = response.data.notes;
            app.subject = response.data.subject;

            //format session data
            for(var i=0;i<app.session_day_attended.length;i++)
            {
                app.session_day_attended[i].date = app.formatDate(app.session_day_attended[i].date,
                                                                        app.session_day_attended[i].enable_time);
                app.session_day_attended[i].earnings = parseFloat(app.session_day_attended[i].earnings).toFixed(2);
                app.session_day_attended[i].show_up_fee = parseFloat(app.session_day_attended[i].show_up_fee).toFixed(2);
            } 

            for(var i=0;i<app.session_day_upcoming.length;i++)
            {
                app.session_day_upcoming[i].date = app.formatDate(app.session_day_upcoming[i].date,
                                                                        app.session_day_upcoming[i].enable_time);
                app.session_day_upcoming[i].earnings = parseFloat(app.session_day_upcoming[i].earnings).toFixed(2);
                app.session_day_upcoming[i].show_up_fee = parseFloat(app.session_day_upcoming[i].show_up_fee).toFixed(2);
            }

            for(var i=0;i<app.notes.length;i++)
            {
                app.notes[i].date = app.formatDate(app.notes[i].date, true);
            }

            app.institutionsList="";
            //create institution list
            for(var i=0;i<app.institutions.length;i++)
            {
                if(i>0)
                {
                    app.institutionsList += ", ";
                }

                app.institutionsList += app.institutions[i].name;
            }

            app.working = false;
        },

        // show the full invitation list
        showInvitations: function(value){
            app.showInvitationsText='<i class="fa fa-spinner fa-spin" aria-hidden="true"></i>';
            app.working = true;
            
            axios.post('/userInfo/{{id}}/', {
                    status :"getInvitations",                                                                                                                        
                })
                .then(function (response) {     
                    app.invitations = response.data.invitations;
                    app.noInvitationsFoundText = "No invitations found"

                    for(var i=0;i<app.invitations.length;i++)
                    {
                        app.invitations[i].date = app.formatDate(app.invitations[i].date,
                                                                        app.invitations[i].enable_time );
                        app.invitations[i].earnings = parseFloat(app.invitations[i].earnings).toFixed(2);
                        app.invitations[i].show_up_fee = parseFloat(app.invitations[i].show_up_fee).toFixed(2);
                    }

                    app.showInvitationsText='Show <i class="fa fa-eye fa-xs"></i>';
                    app.working = false;
                })
                .catch(function (error) {
                    console.log(error);                            
                }); 
        },

        //show traits
        showTraits:function(){
            app.showTraitsButtonText='<i class="fa fa-spinner fa-spin" aria-hidden="true"></i>';
            app.working = true;

            axios.post('/userInfo/{{id}}/', {
                    status :"getTraits",                                                                                                                        
                })
                .then(function (response) {     
                    app.subject_traits = response.data.subject_traits;
                    app.noTraitsFoundText = "No traits found"
                                                
                    app.showTraitsButtonText='Show <i class="fa fa-eye fa-xs"></i>';
                    app.working = false;
                })
                .catch(function (error) {
                    console.log(error);                            
                });
        },

        //delete the selected note
        deleteNote:function(id){
            app.working = true;

            axios.post('/userInfo/{{id}}/', {
                    status : "deleteNote",
                    id : id,                                                                                                                
                })
                .then(function (response) {     
                    app.takeGetSessions(response);
                    app.working = false;                            
                })
                .catch(function (error) {
                    console.log(error);                            
                });
        },

        //make a not about the subject
        sendMakeNote:function(){
            
            if(app.noteText == '') return;
            app.working = true;

            axios.post('/userInfo/{{id}}/', {
                    status : "makeNote",
                    text : app.noteText,                                                                                                                
                })
                .then(function (response) {     
                    app.takeGetSessions(response);
                    $('#noteModalCenter').modal('toggle');
                    app.noteText = "";
                    app.working = false;
                })
                .catch(function (error) {
                    console.log(error);                            
                });
        },

        // fire when edit note model is shown
        showMakeNote:function(){
            
            $('#noteModalCenter').modal('show');
            
        },

        //fire when note model hides
        hideMakeNote:function(){
            
        },

        // fire when edit subject model is shown
        showEditSubject:function(){
            $('#editSubjectModal').modal('show');  
        },

        //fire when subject model hides
        hideEditSubject:function(){
            
        },

        //make a not about the subject
        sendEditSubject: function(){                       
            axios.post('{{ request.path }}', {
                    status :"editSubject" ,                                
                    formData : $("#EditSubjectForm").serializeArray(),                                                              
                })
                .then(function (response) {     
                                                                           
                    status=response.data.status; 
                    // app.clearMainFormErrors();

                    if(status=="success")
                    {                                 
                        location.reload();
                    }
                    else
                    {   
                        console.log("Edit subject errors: " + response.data.errors);                             
                        app.displayErrors(response.data.errors);
                    }          
            
                })
                .catch(function (error) {
                    console.log(error);

                });                        
        },

        //displays to the form errors
        displayErrors:function(errors){
            for(var e in errors)
            {
                $("#id_" + e).attr("class","form-control is-invalid")
                var str='<span id=id_errors_'+ e +' class="text-danger">';
                
                for(var i in errors[e])
                {
                    str +=errors[e][i] + '<br>';
                }

                str+='</span>';
                $("#div_id_" + e).append(str);  

                var elmnt = document.getElementById("div_id_" + e);
                elmnt.scrollIntoView();   
            }
        },

        formatDate: function(value, enable_time){
                if (value) {        
                    if(enable_time)
                    {                    
                        return moment(String(value)).local().format('M/D/YYYY, h:mm a');
                    }
                    else
                    {
                        return moment(String(value)).local().format('M/D/YYYY') + ", Anytime";
                    }

                }
                else{
                    return "date format error";
                }
            },    
    },

    mounted(){
            this.getSessions();  
            $('#noteModalCenter').on("hidden.bs.modal", this.hideMakeNote);       
            $('#editSubjectModal').on("hidden.bs.modal", this.hideEditSubject);           
    },
}).mount('#app');
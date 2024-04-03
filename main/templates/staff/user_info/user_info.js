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
        working:'false',
        su:{%if user.is_staff%}true{%else%}false{%endif%},
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
                app.$data.searching=false;
            });                        
        },

        //process get session response
        takeGetSessions:function(response)
        {
            app.$data.session_day_attended = response.data.session_day_attended;
            app.$data.session_day_upcoming = response.data.session_day_upcoming;  
            app.$data.institutions = response.data.institutions;     
            app.$data.notes = response.data.notes;

            //format session data
            for(var i=0;i<app.$data.session_day_attended.length;i++)
            {
                app.$data.session_day_attended[i].date = app.formatDate(app.$data.session_day_attended[i].date,
                                                                        app.$data.session_day_attended[i].enable_time);
                app.$data.session_day_attended[i].earnings = parseFloat(app.$data.session_day_attended[i].earnings).toFixed(2);
                app.$data.session_day_attended[i].show_up_fee = parseFloat(app.$data.session_day_attended[i].show_up_fee).toFixed(2);
            } 

            for(var i=0;i<app.$data.session_day_upcoming.length;i++)
            {
                app.$data.session_day_upcoming[i].date = app.formatDate(app.$data.session_day_upcoming[i].date,
                                                                        app.$data.session_day_upcoming[i].enable_time);
                app.$data.session_day_upcoming[i].earnings = parseFloat(app.$data.session_day_upcoming[i].earnings).toFixed(2);
                app.$data.session_day_upcoming[i].show_up_fee = parseFloat(app.$data.session_day_upcoming[i].show_up_fee).toFixed(2);
            }

            for(var i=0;i<app.$data.notes.length;i++)
            {
                app.$data.notes[i].date = app.formatDate(app.$data.notes[i].date, true);
            }

            app.$data.institutionsList="";
            //create institution list
            for(var i=0;i<app.$data.institutions.length;i++)
            {
                if(i>0)
                {
                    app.$data.institutionsList += ", ";
                }

                app.$data.institutionsList += app.$data.institutions[i].name;
            }

            app.$data.working = false;
        },

        // show the full invitation list
        showInvitations: function(value){
            app.$data.showInvitationsText='<i class="fa fa-spinner fa-spin" aria-hidden="true"></i>';
            app.$data.working = true;
            
            axios.post('/userInfo/{{id}}/', {
                    status :"getInvitations",                                                                                                                        
                })
                .then(function (response) {     
                    app.$data.invitations = response.data.invitations;
                    app.$data.noInvitationsFoundText = "No invitations found"

                    for(var i=0;i<app.$data.invitations.length;i++)
                    {
                        app.$data.invitations[i].date = app.formatDate(app.$data.invitations[i].date,
                                                                        app.$data.invitations[i].enable_time );
                        app.$data.invitations[i].earnings = parseFloat(app.$data.invitations[i].earnings).toFixed(2);
                        app.$data.invitations[i].show_up_fee = parseFloat(app.$data.invitations[i].show_up_fee).toFixed(2);
                    }

                    app.$data.showInvitationsText='Show <i class="fa fa-eye fa-xs"></i>';
                    app.$data.working = false;
                })
                .catch(function (error) {
                    console.log(error);                            
                }); 
        },

        //show traits
        showTraits:function(){
            app.$data.showTraitsButtonText='<i class="fa fa-spinner fa-spin" aria-hidden="true"></i>';
            app.$data.working = true;

            axios.post('/userInfo/{{id}}/', {
                    status :"getTraits",                                                                                                                        
                })
                .then(function (response) {     
                    app.$data.subject_traits = response.data.subject_traits;
                    app.$data.noTraitsFoundText = "No traits found"
                                                
                    app.$data.showTraitsButtonText='Show <i class="fa fa-eye fa-xs"></i>';
                    app.$data.working = false;
                })
                .catch(function (error) {
                    console.log(error);                            
                });
        },

        //delete the selected note
        deleteNote:function(id){
            app.$data.working = true;

            axios.post('/userInfo/{{id}}/', {
                    status : "deleteNote",
                    id : id,                                                                                                                
                })
                .then(function (response) {     
                    app.takeGetSessions(response);
                    app.$data.working = false;                            
                })
                .catch(function (error) {
                    console.log(error);                            
                });
        },

        //make a not about the subject
        sendMakeNote:function(){
            
            if(app.$data.noteText == '') return;
            app.$data.working = true;

            axios.post('/userInfo/{{id}}/', {
                    status : "makeNote",
                    text : app.$data.noteText,                                                                                                                
                })
                .then(function (response) {     
                    app.takeGetSessions(response);
                    $('#noteModalCenter').modal('toggle');
                    app.$data.noteText = "";
                    app.$data.working = false;
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
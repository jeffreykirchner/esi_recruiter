axios.defaults.xsrfHeaderName = "X-CSRFTOKEN";
axios.defaults.xsrfCookieName = "csrftoken";

var app = new Vue({

    delimiters: ['[[', ']]'],
    el: '#root',        
    data:{

        waiting:false,
        current_invitation:null,

        consent_form:{{consent_form_json|safe}},
        consent_form_subject:{{consent_form_subject_json|safe}},

        pixi_app:null,
        pixi_pointer_down:false,        
        pixi_signatures_rope_array:[],
        pixi_signature_texture:null,

        consent_form_error:"",
    },

    methods:{

        acceptConsentForm:function(){

            app.$data.consent_form_error = "";

            consent_form_signature = {};
            consent_form_signature_resolution = {};

            if(app.$data.current_invitation.consent_form.signature_required)
            {
                if(app.$data.pixi_signatures_rope_array.length==0)
                {
                    app.$data.consent_form_error = "Sign before accepting.";
                    return;
                } 

                for(i=0;i<app.$data.pixi_signatures_rope_array.length;i++)
                {
                    consent_form_signature[i]=app.$data.pixi_signatures_rope_array[i].points;
                }

                let canvas = document.getElementById('signature_canvas_id');

                consent_form_signature_resolution['width']=canvas.width;
                consent_form_signature_resolution['height']=canvas.height;
            }

            app.$data.waiting=true;

            axios.post('/subjectHome/', {
                            action :"acceptConsentForm",        
                            consent_form_id : app.$data.current_invitation.consent_form.id, 
                            consent_form_signature : consent_form_signature, 
                            consent_form_signature_resolution : consent_form_signature_resolution,                                                                                                                                                      
                        })
                        .then(function (response) {     
                            app.takeUpcomingInvitations(response);
                            app.takePastAcceptedInvitations(response);

                            if(app.$data.current_invitation)
                            {
                                let found = false;
                                for(let i=0;i<app.$data.upcomingInvitations.length;i++)
                                {
                                    if(app.$data.current_invitation.id == app.$data.upcomingInvitations[i].id)
                                    {
                                        app.$data.current_invitation = app.$data.upcomingInvitations[i];
                                        found=true;
                                        break;
                                    }
                                }

                                if(!found)
                                {
                                    for(let i=0;i<app.$data.pastAcceptedInvitations.length;i++)
                                    {
                                        if(app.$data.current_invitation.id == app.$data.pastAcceptedInvitations[i].id)
                                        {
                                            app.$data.current_invitation = app.$data.pastAcceptedInvitations[i];
                                            found=true
                                            break;
                                        }
                                    }
                                }

                                app.$data.waiting=false;
                            }
                        })
                        .catch(function (error) {
                            console.log(error);                                    
                        });                        
        },
        
        handleResize:function(){
            if(app.$data.current_invitation)
            {
                
            }
            app.resetPixiApp();
        },

        {%include "subject/consent_form/pixi_setup.js"%}
  
    },


    mounted: function(){
        setTimeout(this.resetPixiApp, 500);
        window.addEventListener('resize', this.handleResize);     
    },
});

// pixi app
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

            if(app.$data.consent_form_subject)
            {
                app.$data.consent_form_error = "Refresh the page.";
                return;
            }

            app.$data.consent_form_error = "";

            consent_form_signature = {};
            consent_form_signature_resolution = {};

            if(app.$data.consent_form.signature_required)
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

            axios.post('{{request.get_full_path}}', {
                            action :"acceptConsentForm",        
                            consent_form_id : app.$data.consent_form.id, 
                            consent_form_signature : consent_form_signature, 
                            consent_form_signature_resolution : consent_form_signature_resolution,                                                                                                                                                      
                        })
                        .then(function (response) {     

                            app.$data.consent_form_subject = response.data.consent_form_subject_json;                                
                            app.$data.waiting=false;
                            
                        })
                        .catch(function (error) {
                            console.log(error);                                    
                        });                        
        },
        
        handleResize:function(){      
            if(app.$data.consent_form_subject)
            {
                app.resetPixiApp();
            } 
        },

        {%include "subject/consent_form/pixi_setup.js"%}
  
    },


    mounted: function(){
        setTimeout(this.resetPixiApp, 500);
        window.addEventListener('resize', this.handleResize);     
    },
});

// pixi app
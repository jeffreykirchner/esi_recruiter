{% load static %}
"use strict";
axios.defaults.xsrfHeaderName = "X-CSRFTOKEN";
axios.defaults.xsrfCookieName = "csrftoken";

let app = Vue.createApp({

    delimiters: ['[[', ']]'],
       
    data(){return{                
        subject_list:[],
        experiment_list : [],
        working:false,
        consent_form_choice:null,
        consent_form:null,
        counter:0,
        tick_tock:0,
        pixi_app:null,
    }},

    methods:{
        
        //get list of open experiments
        getConsentForm:function getConsentForm(){       

            app.working=true;
            app.subject_list=[];
            app.experiment_list=[];
            app.consent_form=null;

            axios.post('{{ request.path }}', {
                        action :"getConsentForm" ,   
                        formData : {"consent_form":app.consent_form_choice},                                                                                                                          
                        })
                        .then(function (response) {     
                            
                            app.subject_list=response.data.subject_list;                           
                            app.consent_form=response.data.consent_form;
                            app.experiment_list=response.data.experiment_list;

                            app.working=false;

                            setTimeout(app.setupPixi, 500);
                            
                        })
                        .catch(function (error) {
                            console.log(error);
                            
                        });                        
        },

        setupPixi: function setupPixi(){    
            if(!app.consent_form) return;
            if(!app.consent_form.signature_required) return;
        
            app.pixi_signature_texture = PIXI.Texture.from('{% static "signature_4.png" %}');
        
            if(! app.pixi_app)
            {
                app.offScreenCanvas = document.createElement("canvas");
                app.c_width = 200;
                app.c_height = 50;
                app.offScreenCanvas.width = app.c_width;
                app.offScreenCanvas.height = app.c_height;
        
                app.pixi_app = new PIXI.Application({
                    
                    width:app.c_width,
                    height:app.c_height,
        
                    antialias: true,
                    
        
                    view: app.offScreenCanvas });
            }
        
            app.counter=0;
            app.tick_tock=0;
        
            app.pixi_app.ticker.add((delta) => {       
        
                if(app.counter<app.subject_list.length)
                {
                    if(app.tick_tock==0)
                    {
                        app.tick_tock=1;
                        app.resetPixiApp("signature_canvas_id_" + app.subject_list[app.counter].id, 
                                    app.subject_list[app.counter].signature_points,
                                    app.subject_list[app.counter].singnature_resolution)
                    }
                    else
                    {
                        app.tick_tock=0;
        
                        let canvas = document.getElementById("signature_canvas_id_" + app.subject_list[app.counter].id);
                        let temp_c=app.pixi_app.renderer.extract.canvas(app.pixi_app.stage);
                        canvas.getContext("2d").drawImage(temp_c, 0, 0);
        
                        app.counter++;
                    }
                }
                else
                {
                    app.counter=0;
                    app.tick_tock=0;
                }
        
            
            });
        
            // for(let i=0;i<app.sessionDayUsers.length;i++)
            // {
            //     // if(app.sessionDayUsers[i].pixi_app)
            //     // {
            //     //     app.sessionDayUsers[i].pixi_app.destroy();
            //     // }
                
                
            // }
        },
        
        resetPixiApp: function resetPixiApp(canvas_id, signature_points, signature_scale){
            
            app.pixi_app.stage.removeChildren()

            
            for (let i in signature_points) {
        
                let t = signature_points[i];        
        
                let points = [];

                let min_y = 1000;
                let max_y = -1;

                let min_x = 1000;
                let max_x = -1;
        
                for(let j=0;j<t.length;j++)
                {
                    if(t[j].y<min_y) min_y = t[j].y;
                    if(t[j].y>max_y) max_y = t[j].y;

                    if(t[j].x<min_x) min_x = t[j].x;
                    if(t[j].x>max_x) max_x = t[j].x;

                    if(j>0)
                    {
                        if(t[j].x == t[j-1].x)
                        {
                            t[j].x += 0.1;
                        }

                        if(t[j].y == t[j-1].y)
                        {
                            t[j].y += 0.1;
                        }
                    }

                    points.push(new PIXI.Point(t[j].x,
                                               t[j].y))
                }
                
                let r = new PIXI.SimpleRope(app.pixi_signature_texture, points);
                let container = new PIXI.Container();

                container.addChild(r);
        
                //r.scale.x = r.scale.y = app.c_height / signature_scale.height;
                
                if(container.height>0) app.pixi_app.stage.addChild(container);
               
            }  
        },
        
        //load past signature
        clearPixi: function clearPixi(pixi_app,canvas_id){
        
            // let canvas = document.getElementById(canvas_id);
        
            // let background = new PIXI.Graphics();
            // background.beginFill(0xffffff);
            // background.drawRect(0, 0, canvas.width, canvas.height);
            // background.endFill();
        
            pixi_app.stage.removeChildren();
        },
    
    },
        
    mounted(){
                      
    },
    
}).mount('#app');
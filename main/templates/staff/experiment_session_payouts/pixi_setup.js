{% load static %}

/**
 * update the pixi players with new info
 */
setupPixi(){    
    if(app.$data.payGroup!="consent") return;
    if(!app.$data.consentForm) return;
    if(!app.$data.consentForm.signature_required) return;

    app.$data.pixi_signature_texture = PIXI.Texture.from('{% static "signature_4.png" %}');

    if(! app.$data.pixi_app)
    {
        app.$data.offScreenCanvas = document.createElement("canvas");
        app.$data.c_width = 200;
        app.$data.c_height = 50;
        app.$data.offScreenCanvas.width = app.$data.c_width;
        app.$data.offScreenCanvas.height = app.$data.c_height;

        app.$data.pixi_app = new PIXI.Application({
            
            width:app.$data.c_width,
            height:app.$data.c_height,

            antialias: true,
        
            view: app.$data.offScreenCanvas });
    }

    app.$data.counter=0;
    app.$data.tick_tock=0;

    app.$data.pixi_app.ticker.add((delta) => {       

        if(app.$data.counter<app.$data.sessionDayUsers.length)
        {
            if(app.$data.tick_tock==0)
            {
                app.$data.tick_tock=1;
                app.resetPixiApp("signature_canvas_id_" + app.$data.sessionDayUsers[app.$data.counter].id, 
                            app.$data.sessionDayUsers[app.$data.counter].profile_consent_form.signature_points,
                            app.$data.sessionDayUsers[app.$data.counter].profile_consent_form.singnature_resolution)
            }
            else
            {
                app.$data.tick_tock=0;

                let canvas = document.getElementById("signature_canvas_id_" + app.$data.sessionDayUsers[app.$data.counter].id);
                temp_c=app.$data.pixi_app.renderer.extract.canvas(app.$data.pixi_app.stage);
                canvas.getContext("2d").drawImage(temp_c, 0, 0);

                app.$data.counter++;
            }
        }
        else
        {
            app.$data.counter=0;
            app.$data.tick_tock=0;
        }

    
    });

    for(let i=0;i<app.$data.sessionDayUsers.length;i++)
    {
        // if(app.$data.sessionDayUsers[i].pixi_app)
        // {
        //     app.$data.sessionDayUsers[i].pixi_app.destroy();
        // }
        
        
    }
},

resetPixiApp(canvas_id, signature_points, signature_scale){
    
    app.$data.pixi_app.stage.removeChildren()
    
    if(app.$data.payGroup=="consent")
    for (let i in signature_points) {

        let t = signature_points[i];        

        let points = [];

        for(let j=0;j<t.length;j++)
        {
            points.push(new PIXI.Point(t[j].x,
                                       t[j].y))
        }
            
        r = new PIXI.SimpleRope(app.$data.pixi_signature_texture, points);

        //r.scale.x = r.scale.y = app.$data.c_height / signature_scale.height;

        app.$data.pixi_app.stage.addChild(r);
    }    
},

//load past signature
clearPixi(pixi_app,canvas_id){

    // let canvas = document.getElementById(canvas_id);

    // let background = new PIXI.Graphics();
    // background.beginFill(0xffffff);
    // background.drawRect(0, 0, canvas.width, canvas.height);
    // background.endFill();

    pixi_app.stage.removeChildren();
},


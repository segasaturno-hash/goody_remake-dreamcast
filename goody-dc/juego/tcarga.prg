// Prueba de Goody: las 32 fases seguidas desde la precarga en RAM. Para cada una:
// fpg_load, dibujar todos sus mapas a la vez (crea las texturas), RAM y VRAM libres.
import "libmod_gfx";
import "libmod_misc";
import "libmod_dreamcast";

global int f; int tex_ms; end

process mapa( int fic, int g, int px, int py )
begin
    file = fic; graph = g; x = px; y = py; size = 20;
    loop frame; end
end

process main()
private int t, i, j, d, peor_ram = 99999999, peor_vram = 99999999, peor_ms; string n; end
begin
    set_mode( 640, 480 );
    dc_preload( "data1/niv_*.fpg" );
    dc_preload( "data1/dur_*.png" );
    dc_preload( "data2/musica1.gdt" );
    say( "[TC] precarga " + ( dc_preload_total() / 1024 ) + " KB, ram libre " + ( dc_ram_free() / 1024 ) + " KB" );
    for ( i = 0; i < 32; i++ )
        n = "data1/niv_" + ( i / 10 ) + ( i % 10 ) + ".fpg";
        t = dc_time_ms();
        f = fpg_load( n );
        d = map_load( "data1/dur_" + ( i / 10 ) + ( i % 10 ) + ".png" );
        t = dc_time_ms() - t;
        n = "";
        for ( j = 1; j < 100; j++ ) if ( map_exists( f, j ) ) mapa( f, j, 100 + j * 4, 240 ); n += " " + j; end end
        say( "[TC] f=" + f + " mapas:" + n );
        tex_ms = dc_time_ms(); frame; tex_ms = dc_time_ms() - tex_ms;
        frame;
        say( "[TC] fase " + i + ": carga " + t + " ms, texturas " + tex_ms + " ms, ram libre " + ( dc_ram_free() / 1024 ) + " KB, vram libre " + ( dc_vram_free() / 1024 ) + " KB" );
        if ( dc_ram_free() < peor_ram ) peor_ram = dc_ram_free(); end
        if ( dc_vram_free() < peor_vram ) peor_vram = dc_vram_free(); end
        if ( t + tex_ms > peor_ms ) peor_ms = t + tex_ms; end
        signal( type mapa, s_kill );
        frame;
        fpg_unload( f ); map_unload( 0, d );
        frame;
    end
    say( "[TC] FIN: peor ram libre " + ( peor_ram / 1024 ) + " KB, peor vram libre " + ( peor_vram / 1024 ) + " KB, peor cambio " + peor_ms + " ms" );
    loop frame; end
end

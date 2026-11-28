package com.exvius.local;
import java.nio.file.*;
import java.util.*;
import android.content.Context;
import com.chaquo.python.Python;

public final class PreNativeProfile112Test extends PopulatedProfileTest {
    static int passed;
    static void expect(String label, Change change, String expected) throws Exception {
        setup();
        try {
            fixture(); change.run(); Map<String,String> old=snapshot();
            String result=NativeStartupTrial.preNativePopulatedInspection112(c);
            if(!result.contains(expected)||!snapshot().equals(old)||NativeStartupTrial.admitted()||NativeStartupTrial.claimed())
                throw new AssertionError(label+": "+result);
            if(result.contains("PRIVATE_PLAYER_MARKER")||result.contains(root.toString()))throw new AssertionError("private data exposed");
            System.out.println("PASS "+label); passed++;
        } finally { Python.started=false; clean(); }
    }
    static void race(String label, Path target, String replacement) throws Exception {
        Context original=c;
        c=new Context(){ int reads;
            @Override public java.io.File getFilesDir(){
                if(++reads==2)try{Files.writeString(target,replacement);}catch(Exception e){throw new IllegalStateException(e);}
                return files;
            }
        };
        c.files=original.files; c.app.dataDir=original.app.dataDir;
        String result=NativeStartupTrial.preNativePopulatedInspection112(c);
        if(!result.contains("profile evidence stability")||NativeStartupTrial.claimed()||NativeStartupTrial.admitted()||!Files.readString(target).equals(replacement))throw new AssertionError(label+": "+result);
        System.out.println("PASS "+label);passed++;
    }
    public static void main(String[] args)throws Exception {
        expect("valid populated profile remains read-only and HOLD",()->{},"PASS; runtime admission HOLD");
        expect("existing Python rejected before inspection",()->Python.started=true,"Python cold-start check");
        expect("non-main process rejected",()->c.pkg="wrong.package","package and UID identity");
        expect("campaign recovery sidecar preserved",()->Files.writeString(campaign.resolveSibling("campaign.json.tmp"),"fixture"),"populated state inventory");
        expect("catalogue recovery sidecar preserved",()->Files.writeString(index.resolveSibling("index.json.bak"),INITIAL),"populated catalogue inventory");
        expect("malformed campaign preserved",()->Files.writeString(campaign,"{}"),"populated campaign identity and structure");
        expect("registry mismatch preserved",()->Files.writeString(xml,XML.replace("two","other")),"registry preference value mismatch");
        setup();try{fixture();race("valid campaign changed between snapshots",campaign,CAMPAIGN+"\n");}finally{clean();}
        setup();try{fixture();race("valid catalogue changed between snapshots",index,INITIAL.replace("\"label\":\"\"","\"label\":\"fixture\""));}finally{clean();}
        setup();try{fixture();race("valid preference bytes changed between snapshots",xml,XML+"\n");}finally{clean();}
        setup();try{fixture();race("valid registry bytes changed between snapshots",registry,JSON+"\n");}finally{clean();}
        setup();try{fixture();NativeStartupTrial.claim();Map<String,String> old=snapshot();String r=NativeStartupTrial.preNativePopulatedInspection112(c);if(!r.contains("cold startup inspection")||!r.contains("BLOCKED")||NativeStartupTrial.admitted()||!old.equals(snapshot()))throw new AssertionError(r);System.out.println("PASS claimed process refused without writes");passed++;}finally{clean();}
        System.out.println(passed+"/12 PASS — mock Android, original retained validators, no native admission");
    }
}
